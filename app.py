#!/usr/bin/python
#-*- coding: utf-8 -*-

import pandas as pd 
import re
import requests
import sys
import numpy
import math
import string

from bs4 import BeautifulSoup
from flask import Flask, render_template, redirect, url_for, request
from elasticsearch import Elasticsearch
from werkzeug.utils import secure_filename
from nltk import word_tokenize
from nltk.corpus import stopwords

app = Flask(__name__)

host = '127.0.0.1'
port = '8000'
es_port = "9200"   
es = Elasticsearch([{'host':host, 'port':es_port}], timeout=30)
swlist = []

def compute_idf(dictionary, sent_list):
    Dval = len(sent_list)

    idf_d = {}
    for t in dictionary:
        cnt = 0
        for s in sent_list: 
            if t in word_tokenize(s): # 문장을 자르는 방법은 word_tokenize()
                cnt += 1
            if cnt:
                idf_d[t] = math.log(Dval / cnt)

    return idf_d

def compute_tf(dictionary, s):
    
    tf_d = {}

    for word, count in dictionary.items():
        tf_d[word] = float(count) / float(len(dictionary))

    return tf_d

# tfidf: 값이 저장 되는 곳
# dictionary: 유의미한 단어의 딕셔너리
# sent_list: 유의미한 문장의 리스트
def analyze(tfidf, dictionary, sent_list): 
    idf_d = compute_idf(dictionary, sent_list)

    for i in range(0, len(sent_list)):
        tf_d = compute_tf(dictionary, sent_list[i])
        for word, tfval in tf_d.items():
            tfidf[word] = tfval * idf_d[word]
            
    res = sorted(tfidf.items(), key=(lambda x: x[1]), reverse=True)
    top10 = dict(res[:10]) # top10을 뽑음
    
    return top10


def insertDoc(url, dictionary): # ElasticSearch에 저장
    i = 1
    for word in dictionary:
        doc = {
            "url": url,
            "words" : word,
            "frequency": dictionary[word],
        }
        es.index(index='web', doc_type="word", id=i, body=doc)
        i += 1

# allWords: 총 단어가 저장되는 리스트
# dictionary: 유의한 단어를 저장할 리스트
# sent_list: 유의미(문장부호 등이 없는)한 문장이 저장되어 있는 리스트
def findWords(allWords, dictionary, sent_list):
    for sentence in sent_list:
        textSlice = word_tokenize(sentence)
        for word in textSlice:
            if word:
                try: allWords[word] += 1
                except: allWords[word] = 1
                if word not in swlist:
                    try: dictionary[word] += 1
                    except: dictionary[word] = 1

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

def webcrawl(url):
    res = requests.get(url)
    html = BeautifulSoup(res.content, "html.parser")

    allWords = {} # 사이트에 있는 모든 글자
    dictionary = {} # 분석에 사용할 유의미한 글자
    html_body = [] # 크롤링할 내용이 저장될 리스트
    sent_list = [] # 크롤링한 내용의 문장들이 저장되는 리스트
    tfidf = {} # tfidf 결과가 저장되는 딕셔너리

    html_body = html.select('body') # 웹 페이지 전부 크롤링
    findSentList(html_body, sent_list) # 크롤링한 데이터를 문장 단위로 추출
    findWords(allWords, dictionary, sent_list)  # 문장 단위로 추출한 데이터를 단어 단위로 추출
    # allWords는 전체 단어의 갯수, dictionary는 유의한 단어의 갯수

    # insertDoc(url, dictionary)

    top10 = analyze(tfidf, dictionary, sent_list)
    print(len(allWords))
    print(allWords)
    print(len(dictionary))
    print(dictionary)

    return top10

@app.route('/')
def render_file():
    return render_template('home.html')

@app.route('/file_uploaded', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file1']
        txt = request.form['text1']
        dictionary = []
        if f: # 파일로 받으면 여기로
            urls = f.read()
            i = 0
            for url in urls:
                url.replace("\n", "")
                dictionary[i] = webcrawl(url)
                i += 1
            return dictionary
        if txt: # 텍스트 하나만 받으면 여기로
            url = txt
            url.replace("\n", "")
            dictionary = webcrawl(url)
            return dictionary

if __name__ == '__main__':
    # debug를 True로 세팅하면, 해당 서버 세팅 후에 코드가 바뀌어도 문제없이 실행됨. 
    for sw in stopwords.words("english"):
        swlist.append(sw)
    
    app.run(host, port, debug=True)