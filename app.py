from flask import Flask, redirect, url_for, request, render_template
from werkzeug.utils import secure_filename
import pandas as pd 

app = Flask(__name__)


@app.route('/')
def render_file():
    return render_template('home.html')

@app.route('/file_uploaded', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file1']
        txt = request.form['text1']
        if f:
            df_to_html = f.read()
        if txt:
            df_to_html = txt
        return df_to_html

if __name__ == '__main__':
    # debug를 True로 세팅하면, 해당 서버 세팅 후에 코드가 바뀌어도 문제없이 실행됨. 
    app.run(host='127.0.0.1', port=8000, debug = True)