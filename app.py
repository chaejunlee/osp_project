#!/usr/bin/python
#-*- coding: utf-8 -*-

import pandas as pd 
import re
import requests
import sys
import numpy

from bs4 import BeautifulSoup
from flask import Flask, render_template, redirect, url_for, request
from elasticsearch import Elasticsearch
from werkzeug.utils import secure_filename
from nltk import word_tokenize

app = Flask(__name__)

host = '127.0.0.1'
port = '8000'
es_port = "9200"   
es = Elasticsearch([{'host':host, 'port':es_port}], timeout=30)

def insertDoc(url, dictionary):
    i = 1
    print(dictionary)
    for word in dictionary:
        doc = {
            "url": url,
            "words" : word,
            "frequency": dictionary[word],
        }
        print(doc)
        res = es.index(index='web', doc_type="word", id=i, body=doc)
        i += 1
        print(res)

def findWords(html_body, dictionary):
    for sentence in html_body:
        body = sentence.text
        textSlice = body.split()
        for word in textSlice:
            cleanWord = re.sub('[^0-9a-zA-Z]', '', word)
            if cleanWord:
                try: dictionary[cleanWord] += 1
                except: dictionary[cleanWord] = 1

def webcrawl(url):
    res = requests.get(url)
    html = BeautifulSoup(res.content, "html.parser")

    dictionary = {}
    html_body = []

    html_body = html.select('body')
    findWords(html_body, dictionary)
    
    

    insertDoc(url, dictionary)

    return dictionary

@app.route('/')
def render_file():
    return render_template('home.html')

@app.route('/file_uploaded', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file1']
        txt = request.form['text1']
        dictionary = []
        if f:
            urls = f.read()
            i = 0
            for url in urls:
                url.replace("\n", "")
                dictionary[i] = webcrawl(url)
                i += 1
            return dictionary
        if txt:
            url = txt
            url.replace("\n", "")
            dictionary = webcrawl(url)
            return dictionary

if __name__ == '__main__':
    # debug를 True로 세팅하면, 해당 서버 세팅 후에 코드가 바뀌어도 문제없이 실행됨. 
    app.run(host, port, debug = True)