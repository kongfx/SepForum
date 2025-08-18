import json
import time

import captcha.image
import datetime

from flask import flash, request, redirect, url_for, g
from flask_login import current_user, logout_user

from db import DBSession
from .. import db
from . import main

captcha_fn = captcha.image.ImageCaptcha()

@main.app_context_processor
def context_processor():
    return dict(timestamp=datetime.datetime.now().timestamp(), Permission=db.Permission)



@main.app_before_request
def before_request():
    g.dbs = DBSession()
    # print(request.path)
    if current_user.is_authenticated and current_user.banned and current_user.perm & db.Permission.ADMINISTRATOR == 0:
        flash(f'封禁用户，申诉微信/线下联系。你已被登出。理由：' + current_user.ban_reason)
        logout_user()
    if current_user.is_authenticated and not current_user.confirmed and (
            request.endpoint != "static") and not request.path.startswith(
        "/auth") and request.endpoint != 'gen_captcha':
        # flash("")
        return redirect(url_for('unconfirmed'))

    if current_user.is_authenticated:
        g.user_ip = request.remote_addr
        g.endpoint = request.endpoint
        g.url = request.url
        if 'auth' not in g.url and request.endpoint != 'static' and request.method == 'POST':
            form = request.form
            form = dict(form)
            try:
                del form['csrf_token']
                del form['password']
            except KeyError:
                pass
            form['type'] = g.endpoint
            g.safe_data = json.dumps(form)
        else:
            g.safe_data = json.dumps({"type": g.endpoint})
        g.operation = db.Operation(user_id=current_user.id, endpoint=g.endpoint, url=g.url, ip=g.user_ip,
                                   data=g.safe_data)
        g.start_time = time.time()


@main.app_teardown_request
def after_request(response):
    if current_user.is_authenticated:
        end_time = time.time()
        try:
            g.operation: db.Operation = g.operation
        except AttributeError:
            return response
        g.operation.time_used = (end_time - g.start_time) * 1000
        if response:
            g.operation.status = response.status_code
        g.dbs.add(g.operation)
        g.dbs.commit()
    g.dbs.close()
    return response