#!/usr/bin/python
# -*- coding: utf-8 -*-

import pandas as pd
import re
import requests
import sys
import numpy
import math
import string
import time
import itertools

from bs4 import BeautifulSoup
from flask import Flask, render_template, redirect, url_for, request, flash
from elasticsearch import Elasticsearch
from werkzeug.utils import secure_filename
from nltk import word_tokenize
from nltk.corpus import stopwords

app = Flask(__name__)

host = 'localhost'
port = '8000'
es_port = "9200"
es = Elasticsearch([{'host': host, 'port': es_port}], timeout=30)
swlist = []

index_list = []

word_d = {}


def compute_idf(dictionary, sent_list):
    Dval = len(sent_list)

    idf_d = {}
    for t in dictionary:
        cnt = 0
        for s in sent_list:
            if t in word_tokenize(s):  # 문장을 자르는 방법은 word_tokenize()
                cnt += 1
            if cnt:
                idf_d[t] = math.log(Dval / cnt)

    return idf_d


def compute_tf(dictionary, s):
    tf_d = {}

    for word, count in dictionary.items():
        tf_d[word] = float(count) / float(len(dictionary))

    return tf_d


def findDict(sent_list):
    dictionary = {}
    for sentence in sent_list:
        textSlice = word_tokenize(sentence)
        for word in textSlice:
            if word:
                if word not in swlist:
                    try:
                        dictionary[word] += 1
                    except:
                        dictionary[word] = 1
    return dictionary

# tfidf: 값이 저장 되는 곳
# dictionary: 유의미한 단어의 딕셔너리
# sent_list: 유의미한 문장의 리스트


def top10Analyze(sent_list):
    dictionary = {}
    tfidf = {}

    dictionary = findDict(sent_list)

    idf_d = compute_idf(dictionary, sent_list)

    for i in range(0, len(sent_list)):
        tf_d = compute_tf(dictionary, sent_list[i])
        for word, tfval in tf_d.items():
            tfidf[word] = tfval * idf_d[word]

    res = sorted(tfidf.items(), key=(lambda x: x[1]), reverse=True)
    top10 = dict(res[:10])  # top10을 뽑음

    return top10, dictionary


def insertDoc(idx, url, dictionary, docType):  # ElasticSearch에 저장
    doc = {}
    if type(dictionary) is dict:
        words = list(dictionary.keys())
        numbers = list(dictionary.values())
        doc = {
            "url": url,
            "words": words,
            "numbers": numbers,
            "type": docType,
        }
        es.index(index=idx, id=docType, body=doc)
    if type(dictionary) is list:
        doc = {
            "url": url,
            "words": dictionary,
            "type": docType,
        }
        es.index(index=idx, id=docType, body=doc)

# allWords: 총 단어가 저장되는 리스트
# dictionary: 유의한 단어를 저장할 리스트
# sent_list: 유의미(문장부호 등이 없는)한 문장이 저장되어 있는 리스트


def findWords(allWords, sent_list):
    totalWordCount = 0
    for sentence in sent_list:
        textSlice = word_tokenize(sentence)
        for word in textSlice:
            if word:
                totalWordCount += 1
                try:
                    allWords[word] += 1
                except:
                    allWords[word] = 1

                if word not in word_d.keys():
                    word_d[word] = 0
                word_d[word] += 1
    return totalWordCount

# html_body: rough하게 크롤링한 데이터가 저장되어 있는 string
# sent_list: html_body로부터 유의미한(문장부호등이 없는) 문장이 저장될 리스트


def findSentList(html_body, sent_list):
    for sentence in html_body:
        body = sentence.text
        sending_list = body.splitlines()
        for word in sending_list:
            if word:
                send = word.strip()
                cleanWord = re.sub('[^0-9a-zA-Z]', ' ', send)
                if cleanWord:
                    sent_list.append(cleanWord)


def make_vector(sent_list):
    v = []
    dictionary = findDict(sent_list)
    tokenized = list(dictionary.keys())
    for w in word_d.keys():
        val = 0
        for t in tokenized:
            if t == w:
                val += 1
        v.append(val)
    return v


def webcrawl(url):
    try:
        res = requests.get(url, timeout=3000)
        html = BeautifulSoup(res.content, "html.parser")
    except:
        index = "Webcrawling Failed"
        elapsedTime = -1
        totalWordCount = -1
        successful = False
        return index, elapsedTime, totalWordCount, successful
    link = url
    url = url.replace("http://", "")
    url = url.replace("https://", "")
    index = url.split(".")
    index = index[0]
    index_list.append(index)
    print(index_list)

    allWords = {}  # 사이트에 있는 모든 글자
    html_body = []  # 크롤링할 내용이 저장될 리스트
    sent_list = []  # 크롤링한 내용의 문장들이 저장되는 리스트
    totalWordCount = 0

    elapsedTime = 0

    start = time.time()  # 시간 측정 시작
    html_body += html.select('body')  # 웹 페이지 전부 크롤링
    findSentList(html_body, sent_list)  # 크롤링한 데이터를 문장 단위로 추출
    # 문장 단위로 추출한 데이터를 단어 단위로 추출
    totalWordCount = findWords(allWords, sent_list)
    # allWords는 전체 단어의 갯수, dictionary는 유의한 단어의 갯수

    insertDoc(index, link, sent_list, 'sent_list')

    elapsedTime = time.time() - start  # 시간 측정끝
    successful = True

    return index, elapsedTime, totalWordCount, successful


@app.route('/')
def render_file():
    return render_template('main.html')


@app.route('/cossimil', methods=['GET', 'POST'])
def cossimilweb():
    if request.method == 'POST':
        index = request.form['cossimil']

    start = time.time()

    if (len(index_list) < 3):
        post = [{
            'number': -1,
            'word': 'too little urls, insert more than 4 urls'
        }]
        return render_template('cossimil.html', posts=post)

    sent_list = []
    posts = []
    top = {}
    top3 = {}
    url = ''
    index_url = ''

    result = es.search(index=index, body={
                       'query': {'match': {'type': 'sent_list'}}})

    for data in result['hits']['hits']:
        original_list = (data['_source'].get('words'))

    v1 = make_vector(original_list)

    for idx in index_list:
        if idx != index:
            result = es.search(
                index=idx, body={'query': {'match': {'type': 'sent_list'}}})

            for data in result['hits']['hits']:
                sent_list = (data['_source'].get('words'))
                url = (data['_source'].get('url'))

            v2 = make_vector(sent_list)

            dotpro = numpy.dot(v1, v2)
            cossimil = dotpro / (numpy.linalg.norm(v1) * numpy.linalg.norm(v2))

            top[url] = cossimil
        else:
            result = es.search(
                index=idx, body={'query': {'match': {'type': 'sent_list'}}})

            for data in result['hits']['hits']:
                index_url = (data['_source'].get('url'))

    top = {k: v for k, v in sorted(top.items(), key=lambda item: item[1], reverse=True)}
    top3 = dict(itertools.islice(top.items(), 3))

    i = 1
    for word, score in top3.items():
        posts += [{
            'number': i,
            'word': word,
            'score': score,
        }]
        i += 1

    end = time.time()

    elapsedTime = end - start

    return render_template('cossimil.html', index = index, url = index_url, elapsedTime = elapsedTime, posts=posts)


@app.route('/top10', methods=['GET', 'POST'])
def top10():
    if request.method == 'POST':
        start = time.time()
        index = request.form['tfidf']

        result = es.search(index=index, body={
                        'query': {'match': {'type': 'sent_list'}}})

        sent_list = []
        posts = []
        url = ''

        for data in result['hits']['hits']:
            sent_list = (data['_source'].get('words'))
            url = (data['_source'].get('url'))

        top, dictionary = top10Analyze(sent_list)

        i = 1
        for word in top:
            posts += [{
                'number': i,
                'word': word,
                'frequency': dictionary[word],
            }]
            i += 1
        
        end = time.time()

        elapsedTime = end - start

        return render_template('top10.html', url = url, index = index, elapsedTime = elapsedTime, posts=posts)


@app.route('/analysis', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        try:
            f = request.files['file1']
        except:
            f = None
        try:
            txt = request.form['text1']
        except:
            txt = None

        if len(index_list):
            index_list.clear()
        if len(word_d):
            word_d.clear()

        posts = []
        url_list = []
        if f:  # 파일로 받으면 여기로
            txt = f.read()
            urls = txt.splitlines()
            for binUrl in urls:
                url = binUrl.decode('utf-8')
                if url not in url_list:
                    try:
                        index, elapsedTime, totalWordCount, successful = webcrawl(url)
                    except Exception:
                        flash('Oops! Something wrong happened!')
                        return render_template('main.html')
                    posts += [{
                        'elapsedTime': elapsedTime,
                        'totalWordCount': totalWordCount,
                        'index': index,
                        'url': url,
                        'successful': successful,
                    }]
                    url_list.append(url)
                else:
                    posts += [{
                        'elapsedTime': -1,
                        'totalWordCount': -1,
                        'index': "Duplicate Link",
                        'url': url,
                        'successful': False,
                    }]
                    url_list.append(url)
            return render_template('result.html', posts=posts, port=port)

        if txt:  # 텍스트 하나만 받으면 여기로
            url = txt
            url.replace("\n", "")
            try:
                index, elapsedTime, totalWordCount, successful = webcrawl(url)
            except Exception:
                flash('Oops! Something wrong happened!')
                return render_template('main.html')

            posts += [{
                'elapsedTime': elapsedTime,
                'totalWordCount': totalWordCount,
                'index': index,
                'url': url,
                'successful': successful,
            }]

            # 리턴하는 값들: 처리시간(elapsedTime), 전체 단어수(totalWordCount), 쿼리 접근을 위한 인덱스(index)
            return render_template('result.html', posts=posts, port=port)


if __name__ == '__main__':
    # debug를 True로 세팅하면, 해당 서버 세팅 후에 코드가 바뀌어도 문제없이 실행됨.
    for sw in stopwords.words("english"):
        swlist.append(sw)

    app.run(host, port, debug=True)
