#!/usr/bin/env python3

import os
import cups

from flask import Flask, render_template, request, Response
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = set(['txt', 'c', 'cpp', 'java', 'py'])

ALLOWED_PRINTERS = ['Room_200', 'Room_200C', 'Room_16', 'Room_17']
AUTH_USERNAME = 'tjioi'
AUTH_PASSWORD = 'whatdoyoumeanidosomuchwork'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

conn = cups.Connection(host='cups2')

def check_auth(username, password):
    return username == AUTH_USERNAME and password == AUTH_PASSWORD

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def list_printers():
    printers = conn.getPrinters()
    return {k: v for k, v in printers.items() if k in ALLOWED_PRINTERS}

@app.route('/', methods=['GET', 'POST'])
def hello_world():
    if request.method == 'POST':
        f = request.files['file']
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return 'Ok, saved.'

    return render_template('index.html', printers=list_printers())

@app.before_request
def check_allowed():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return Response('Log in to print', 401,
                {'WWW-Authenticate': 'Basic realm="Login required"'})

