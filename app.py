#!/usr/bin/python
#-*- coding: utf-8 -*-

import pandas as pd 
import re
import requests
import sys

from bs4 import BeautifulSoup
from flask import Flask, render_template, redirect, url_for, request
from elasticsearch import Elasticsearch
from werkzeug.utils import secure_filename

app = Flask(__name__)

def findWords(html_body):
    dictionary = []
    for sentence in html_body:
        body = sentence.text
        textSlice = body.split()
        for word in textSlice:
            cleanWord = re.sub('[^0-9a-zA-Z]', '', word)
            if cleanWord:
                try: dictionary[cleanWord] += 1
                except: dictionary[cleanWord] = 1
    return dictionary

def webcrawl(url):
    res = requests.get(url)
    html = BeautifulSoup(res.content, "html.parser")

    dictionary = []
    html_body = {}

    html_body = html.select('body > div.topnav > div')
    dictionary += findWords(html_body)
    html_body = html.select('.nav.navbar-nav.navbar-right')
    dictionary += findWords(html_body)
    html_body = html.select('.jumbotron')
    dictionary += findWords(html_body)
    html_body = html.select('body > div.feature-list-group > div > div.row.header')
    dictionary += findWords(html_body)
    html_body = html.select('body > div.feature-list-group > div > div:nth-child(2)')
    dictionary += findWords(html_body)
    html_body = html.select('.col-md-3.col-sm-3.feature-item')
    dictionary += findWords(html_body)
    html_body = html.select('.twitter-follow-button')
    dictionary += findWords(html_body)
    html_body = html.select('.twitter-hashtag-button')
    dictionary += findWords(html_body)
    html_body = html.select('.col-md-8.trademark')
    dictionary += findWords(html_body)
    
    # words = list(dictionary.keys())
    # frequency = list(dictionary.values())
    print(dictionary)

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
    app.run(host='127.0.0.1', port=8000, debug = True)
