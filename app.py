#!/usr/bin/env python3

import os
import shutil
import sys
import tempfile
import subprocess
import binascii
import cups

from flask import Flask, render_template, request, Response, send_from_directory, \
        redirect, url_for, flash, session, abort
from werkzeug.utils import secure_filename

# set up logging
import logging
logging.basicConfig(
        filename='printing.log',
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
)

# upload stuff
dir_path = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = os.path.join(dir_path, 'uploads/')
ALLOWED_EXTENSIONS = set(['txt', 'c', 'cpp', 'java', 'py'])

# config
TEAM_DICT = dict(
        [('team%X' % i, 'Room_16') for i in range(0, 7)] +
        [('team%X' % i, 'Room_17') for i in range(7, 14)]
)

AUTH_USERNAME = 'tjioi'
AUTH_PASSWORD = 'whatdoyoumeanidosomuchwork'

# printing options
PAPER_SIZE = 'letter'
MAX_PAGES = 5

# reset upload folder
shutil.rmtree(UPLOAD_FOLDER)
os.mkdir(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
app.secret_key = '9334fb494ad8dd4a8494fbdbaf6c5acd'

conn = cups.Connection(host='cups2')

logging.debug('app.py started')


def check_auth(username, password):
    return username == AUTH_USERNAME and password == AUTH_PASSWORD

def allowed_file(filename):
    return os.path.splitext(filename)[1].lstrip('.') in ALLOWED_EXTENSIONS

def list_printers():
    ALLOWED_PRINTERS = ['Room_200', 'Room_200C', 'Room_16', 'Room_17', 'Room_18']
    printers = conn.getPrinters()
    return {k: v for k, v in printers.items() if k in ALLOWED_PRINTERS}
    #return printers

def generate_pdf(directory, source, team):
    # convert text to ps
    source_ps = os.path.join(directory, "source.ps")
    cmd = ["a2ps",
       source,
       "--delegate=no",
       "--output=" + source_ps,
       "--medium=%s" % PAPER_SIZE,
       "--portrait",
       "--columns=1",
       "--rows=1",
       "--pages=1-%d" % MAX_PAGES,
       "--header=",
       "--footer=%s" % team,
       "--left-footer=",
       "--right-footer=",
       "-C",
       "--pretty-print",
       #"--highlight-level=heavy",
       #"--pro=color",
    ]
    ret = subprocess.call(cmd, cwd=directory)
    if ret != 0:
        logging.error('a2ps error, command: %s (error %d)' % (cmd, ret))
        raise Exception("Failed to convert text file to ps "
            "with command: %s (error %d)" % (cmd, ret))
    assert os.path.exists(source_ps)

    # convert ps to pdf
    source_pdf = os.path.join(directory, "source.pdf")
    cmd = ["ps2pdf",
        "-sPAPERSIZE=%s" % PAPER_SIZE,
        source_ps,
        source_pdf
    ]
    ret = subprocess.call(cmd, cwd=directory)
    if ret != 0:
        logging.error('ps2pdf error, command: %s (error %d)' % (cmd, ret))
        raise Exception("Failed to convert ps file to pdf "
            "with command: %s (error %d)" % (cmd, ret))

@app.route('/')
def home():
    printers = sorted(list_printers().items())
    return render_template('index.html', printers=printers)

@app.route('/do_print', methods=['POST'])
def do_print():
    team = request.form['team']
    printer = request.form['printer']
    f = request.files['file']

    if not (team and team in TEAM_DICT):
        logging.warn('Invalid team: %s' % team)
        flash('Not printed: Invalid team')
        return render_template('blah.html')

    if not (printer and printer in list_printers()):
        logging.warn('Invalid printer: %s' % printer)
        flash('Not printed: Invalid printer')
        return render_template('blah.html')

    if f and allowed_file(f.filename):
        with tempfile.TemporaryDirectory(dir=app.config['UPLOAD_FOLDER']) as directory:
            relname = secure_filename(f.filename)
            source = os.path.join(directory, relname)
            f.save(source)

            generate_pdf(directory, source, team)
            #return send_from_directory(directory, 'source.pdf')

            try:
                job_id = conn.printFile(
                    printer,
                    os.path.join(directory, 'source.pdf'),
                    relname,
                    {})
            except cups.IPPError as error:
                logging.error('cups.IPPError while printing file: %s' % error)
                flash('Not printed: Error while printing file')
                return render_template('blah.html')
            else:
                logging.info('Printed: team %s, printer %s, filename %s' % (team, printer, source))
                flash('File successfully printed! Job ID: %d' % job_id)
                return render_template('blah.html')

    logging.warn('Invalid file: %s' % f)
    flash('Not printed: Invalid file')
    return render_template('blah.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.before_request
def check_allowed():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return Response('401 Unauthorized: Log in to print', 401,
                {'WWW-Authenticate': 'Basic realm="Login required"'})
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = binascii.hexlify(os.urandom(16)).decode()
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token 

