import datetime
import hashlib
import json
import traceback

from flask import render_template, redirect, request, url_for, abort, g
from flask_login import current_user
from werkzeug.exceptions import HTTPException

from . import main

@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@main.app_errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    tbstr = traceback.format_exc()
    time = datetime.datetime.now().timestamp()
    code = hashlib.md5((tbstr + str(time)).encode('utf-8')).hexdigest()
    user_agent = request.headers.get('User-Agent')
    if current_user.is_authenticated and request.endpoint != "auth.login":
        data = json.loads(g.operation.data)
        data['errid'] = code
        g.operation.data = json.dumps(data)
    print(f'{time}-BF-EXCEPTION-{code}-{user_agent}', file=open('log/wklog.log', 'a+'))
    print(tbstr, file=open('log/wklog.log', 'a+'))
    return render_template('500.html', code=code), 500
