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
idf_d = {}

def make_vector(dictionary, word_d):
    v = []
    tokenized = list(dictionary.keys())
    for w in word_d.keys():
        val = 0
        for t in tokenized:
            if t == w:
                val += 1
        v.append(val)
    return v

@app.route('/cossimil', methods=['GET', 'POST'])
def cossimilweb():
    if request.method == 'POST':
        index = request.form['cossimil']

    start = time.time()

    result = es.search(index="all", body={'query': {'match': {'type': 'index_list'}}})
    for data in result['hits']['hits']:
        index_list = (data['_source'].get('words'))

    if (len(index_list) < 3):
        post = [{
            'number': -1,
            'word': 'too little urls, insert more than 4 urls'
        }]
        return render_template('cossimil.html', posts=post)

    dictionary = {}
    posts = []
    top = {}
    top3 = {}
    url = ''
    index_url = ''
    global word_d

    result = es.search(index=index, body={
                       'query': {'match': {'type': 'dictionary'}}})

    for data in result['hits']['hits']:
        dictionary = (data['_source'].get('dict'))

    if not word_d:
        word_d = getWordD()

    v1 = make_vector(dictionary, word_d)

    for idx in index_list:
        if idx != index:
            result = es.search(
                index=idx, body={'query': {'match': {'type': 'dictionary'}}})

            dictionary.clear()

            for data in result['hits']['hits']:
                dictionary = (data['_source'].get('dict'))
                url = (data['_source'].get('url'))

            v2 = make_vector(dictionary, word_d)

            dotpro = numpy.dot(v1, v2)
            cossimil = dotpro / (numpy.linalg.norm(v1) * numpy.linalg.norm(v2))

            top[url] = cossimil
        else:
            result = es.search(
                index=idx, body={'query': {'match': {'type': 'dictionary'}}})

            for data in result['hits']['hits']:
                index_url = (data['_source'].get('url'))

    top = {k: v for k, v in sorted(top.items(), key=lambda item: item[1], reverse=True)}
    insertDoc(index, url, top, "cossimil")
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

    #insertDoc(index, url, posts, "cossimil")
    #insertDoc(index, url, elapsedTime, "cossimilElapsedTime")

    return render_template('cossimil.html', index = index, url = index_url, elapsedTime = elapsedTime, posts=posts)



@app.route('/top10', methods=['GET', 'POST'])
def top10():
    if request.method == 'POST':
        start = time.time()
        index = request.form['tfidf']

        posts = []
        url = ''
        global word_d
        dictionary = {}
        global idf_d
        tf_d = {}

        result = es.search(index=index, body={'query': {'match': {'type': 'dictionary'}}})

        for data in result['hits']['hits']:
            dictionary = (data['_source'].get('dict'))
            url = (data['_source'].get('url'))

        print('getting word_d')
        if not word_d:
            word_d = getWordD()

        print('computing idf_d')

        if not idf_d:
            idf_d = compute_idf(word_d)

        print('computing tf_d')

        tf_d = compute_tf(dictionary, word_d)

        print('computing tfidf')
        top, tfidf = top10Analyze(tf_d, idf_d)

        insertDoc(index, url, tfidf, 'tfidf')

        i = 1
        for word in top:
            posts += [{
                'number': i,
                'word': word,
                'frequency': dictionary[word],
                'score': tfidf[word],
            }]
            i += 1
        
        end = time.time()

        print('computing tfidf done!')
        elapsedTime = end - start

        return render_template('top10.html', url = url, index = index, elapsedTime = elapsedTime, posts=posts)


def getWordD():
    index_list = []
    word_d = {}
    dictionary = {}

    result = es.search(index="all", body={'query': {'match': {'type': 'index_list'}}})
    for data in result['hits']['hits']:
        index_list = (data['_source'].get('words'))

    for index in index_list:
        result = es.search(index=index, body={'query': {'match': {'type': 'dictionary'}}})
        for data in result['hits']['hits']:
            dictionary = (data['_source'].get('dict'))

            for word in dictionary:
                if word not in word_d:
                    word_d[word] = 0
                word_d[word] += 1
    
    return word_d

def compute_idf(word_d):
    dict_list = []
    idf_d = {}
    index_list = []

    result = es.search(index="all", body={'query': {'match': {'type': 'index_list'}}})
    for data in result['hits']['hits']:
        index_list = (data['_source'].get('words'))
    
    Dval = len(index_list)

    for index in index_list:
        result = es.search(index=index, body={'query': {'match': {'type': 'dictionary'}}})
        for data in result['hits']['hits']:
            dictionary = (data['_source'].get('dict'))
        dict_list.append(dictionary)

    for t in word_d.keys():
        count = 0
        for dictionary in dict_list:
            if t in dictionary.keys():
                count += 1
                idf_d[t] = math.log(Dval / count)
            elif t not in idf_d:
                idf_d[t] = 0.0  

    return idf_d


def compute_tf(dictionary, word_d):
    tf_d = {}

    for word, count in dictionary.items():
        tf_d[word] = float(count) / float(len(word_d))

    return tf_d

def top10Analyze(tf_d, idf_d):
    tfidf = {}

    for word, tfval in tf_d.items():
        tfidf[word] = tfval * idf_d[word]

    res = sorted(tfidf.items(), key=(lambda x: x[1]), reverse=True)
    
    top10 = dict(res[:10])  # top10을 뽑음

    return top10, tfidf

#----------ElasticSearch에 저장----------#

def insertDoc(idx, url, dictionary, docType):  
    doc = {}

#--Dictionary이면 dictionary 그 자체로 저장--#
    if type(dictionary) is dict:
        doc = {
            "url": url,
            "dict": dictionary,
            "type": docType,
        }
        es.index(index=idx, id=docType, body=doc)

#--list이면 list 그 자체로 저장--#
    if type(dictionary) is list:
        doc = {
            "url": url,
            "words": dictionary,
            "type": docType,
        }
        es.index(index=idx, id=docType, body=doc)

#----------------------------------------#

#----------findSentList----------#

def findSentList(html_body):
    sent_list = []
    for sentence in html_body:
#--body에서 <tag> 제거--#
        body = sentence.text
        cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
        body = re.sub(cleanr, '', body)
        sending_list = body.splitlines()
#--<tag> 제거됐지만 혹시나 정리할 것 남으면 정리--#

        for word in sending_list:
            if word:
                send = word.strip()
                cleanWord = re.sub('[^0-9a-zA-Z]', ' ', send)
                if cleanWord:
                    sent_list.append(cleanWord)
    return sent_list

#--------------------------------#

#----------findWords----------#

def findWords(sent_list):
    global word_d
    allWords = {}
    totalWordCount = 0
    dictionary = {}
    for sentence in sent_list:
        textSlice = word_tokenize(sentence)
        for word in textSlice:
            if word:
                word = word.lower()
                totalWordCount += 1
                try:
                    allWords[word] += 1
                except:
                    allWords[word] = 1
                
                if word not in swlist:
                    if word not in dictionary.keys():
                        dictionary[word] = 0
                    dictionary[word] += 1
                    if word not in word_d.keys():
                        word_d[word] = 0
                    word_d[word] += 1
    return totalWordCount, dictionary, allWords

#-----------------------------#

#----------Web Crawling----------#

def webcrawl(url):

#--일단 html의 body 전체를 긁어 오기--#
    try:
        res = requests.get(url, timeout=3000)
        html = BeautifulSoup(res.content, "html.parser")

#--실패(링크가 제대로 되지 않음)하면 "Webcrawling Failed" 리턴--#
    except:
        index = "Webcrawling Failed"
        elapsedTime = -1
        totalWordCount = -1
        successful = False
        return index, elapsedTime, totalWordCount, successful

#--link: elasticsearch에 저장할 링크 주소 그 자체--#
    link = url

#--url: url을 잘 손봐서 index로 만들어 줄 것임--#
    url = url.replace("http://", "")
    url = url.replace("https://", "")
    index = url.split(".")
    index = index[0]
#--index_list: 만든 index를 index_list에다가 저장해줌--#
    index_list.append(index)
    print(index_list)

#--사이트에 있는 모든 글자, stopword까지 포함--#
    allWords = {}

#--크롤링할 내용이 저장될 리스트--#
    html_body = []

#--크롤링한 내용의 "문장"들이 저장되는 리스트--#
    sent_list = []

#--dictionary: 유의미한 단어들만 모아놓은 dict 자료형--#
    dictionary = {}

#--크롤링할 사이트에 있는 단어의 개수를 샐 변수--#
    totalWordCount = 0

    elapsedTime = 0
    start = time.time()  # 시간 측정 시작

#--웹 페이지 전부 크롤링--#
    html_body += html.select('body')

#--sent_list가 리턴값--#
    sent_list = findSentList(html_body)  # 크롤링한 데이터를 문장 단위로 추출
    # print(sent_list)

#--문장 단위로 추출한 데이터를 단어 단위로 추출--#
    totalWordCount, dictionary, allWords = findWords(sent_list)

#--allWords는 전체 단어의 갯수, dictionary는 유의미한 단어의 갯수--#

###################################################
#--sent_list 대신에 dictionary 한번 써보겠음--#
    #insertDoc(index, link, sent_list, 'sent_list')
###################################################

#--allWords: 웹사이트의 모든 단어--#
    insertDoc(index, link, allWords, 'allWords')

#--dictionary: 웹사이트의 모든 유의미한 단어--#
    insertDoc(index, link, dictionary, 'dictionary')
    
#--시간 측정끝--#
    elapsedTime = time.time() - start 

#--elapsedTime, totalWordCount 저장--#
    insertDoc(index, link, elapsedTime, "elapsedTime")
    insertDoc(index, link, totalWordCount, "totalWordCount")

    successful = True

    return index, elapsedTime, totalWordCount, successful

#--------------------------------------------#

@app.route('/analysis', methods=['GET', 'POST'])
def upload_file():
#----------input url(s)----------#
    if request.method == 'POST':
        try:
            f = request.files['file1']
        except:
            f = None
        try:
            txt = request.form['text1']
        except:
            txt = None
#--------------------------------#

########################################################################
#--index_list는 데이터 베이스에 저장하자--#
#--word_d는 데이터 베이스에서 불러와서 필요할 때마다 가져오는 걸로 하자--#
########################################################################
        if len(index_list):
            index_list.clear()
        # if len(word_d):
        #     word_d.clear()


#--posts: result page에 넘겨줄 핵심 정보들을 저장할 리스트--#
#--posts: 'elapsedTime', 'totalWordCount', 'index', 'url', 'successful'--#
        posts = []

#--url_list: 입력 파일에서 중복된 리스트 확인을 위해 만든 리스트--#
        url_list = []

#----------file input----------#
#--파일로 받으면 여기로--#
        if f:
            start = time.time()

            txt = f.read()
            urls = txt.splitlines()

            for binUrl in urls:
#--파일로 받으면 binary로 읽혀서 str로 바꿔주는 과정--#
                url = binUrl.decode('utf-8')

#--아직 입력되지 않은 url이라면--#
                if url not in url_list:

#--webcrawl(url): index(엘라스틱 서치의 index 값), elapsedTime(크롤링에 걸린 시간), totalWordCount(크롤링한 총 단어), successful(크롤링 성공 여부)--#
                    try:
                        index, elapsedTime, totalWordCount, successful = webcrawl(url)
                    except Exception as e:
#--만약 크롤링에서 오류가 났다면 다시 main 페이지 로드--#
                        print(e)
                        return render_template('main.html', error="Something wrong happened. Please Try Again")

#--webcrawl의 결과를 posts에 저장--#
                    posts += [{
                        'elapsedTime': elapsedTime,
                        'totalWordCount': totalWordCount,
                        'index': index,
                        'url': url,
                        'successful': successful,
                    }]

                    url_list.append(url)

#--이미 입력된 url이라면--#
                else:

                    posts += [{
                        'elapsedTime': -1,
                        'totalWordCount': -1,
                        'index': "Duplicate Link",
                        'url': url,
                        'successful': False,
                    }]

                    url_list.append(url)

#--index_list: 엘라스틱 서치에 저장한 데이터들의 index 값--#
            insertDoc("all", "all", index_list, 'index_list')
            # insertDoc("all", "all", word_d, 'word_d')

#--url_list의 길이가 1 이하라면 tf_idf, cossimil의 의미가 없기 때문에 url_len(top10, cossimil 버튼의 활성화 여부)를 False로 한다.--#
            if (len(url_list) < 2):
                url_len = False
            else:
                url_len = True
            
            totalTime = time.time() - start
#--결과에 대해 result.html을 렌더링 한다.--#
            return render_template('result.html', posts=posts, url_len=url_len, totalTime=totalTime)


#----------single url input----------#
#--텍스트 하나만 받으면 여기로--#
        if txt:

#--간단하게 정리해주고--#
            url = txt
            url.replace("\n", "")
            start = time.time()

            try:
#--webcrawl(url): index(엘라스틱 서치의 index 값), elapsedTime(크롤링에 걸린 시간), totalWordCount(크롤링한 총 단어), successful(크롤링 성공 여부)--#
                index, elapsedTime, totalWordCount, successful = webcrawl(url)

#--만약 크롤링에서 오류가 났다면 다시 main 페이지 로드--#
            except Exception:
                return render_template('main.html', error="Something wrong happened.<br>Please try again.")

#--webcrawl의 결과를 posts에 저장--#
            posts += [{
                'elapsedTime': elapsedTime,
                'totalWordCount': totalWordCount,
                'index': index,
                'url': url,
                'successful': successful,
            }]

#--리턴하는 값들: 처리시간(elapsedTime), 전체 단어수(totalWordCount), 쿼리 접근을 위한 인덱스(index)--#
            insertDoc("all", "all", index_list, 'index_list')
            # insertDoc("all", "all", word_d, 'word_d')

#--url_list의 길이가 1 이하라면 tf_idf, cossimil의 의미가 없기 때문에 url_len(top10, cossimil 버튼의 활성화 여부)를 False로 한다.--#
            if (len(url_list) < 2):
                url_len = False
            else:
                url_len = True

            totalTime = time.time() - start

#--결과에 대해 result.html을 렌더링 한다.--#
            return render_template('result.html', posts=posts, url_len=url_len, totalTime=totalTime)

#--만약 크롤링에서 오류가 났다면 다시 main 페이지 로드--#
        return render_template('main.html', error="Something wrong happened.<br>Please try again.")

#--------------------------------------#

@app.route('/')
def render_file():
    return render_template('main.html')

if __name__ == '__main__':
    # debug를 True로 세팅하면, 해당 서버 세팅 후에 코드가 바뀌어도 문제없이 실행됨.
    for sw in stopwords.words("english"):
        swlist.append(sw)

    app.run(host, port, debug=True)