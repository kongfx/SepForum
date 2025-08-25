import json
import math
import time

import bleach
import captcha.image
import datetime

from flask import flash, request, redirect, url_for, g, render_template, abort
from flask_login import current_user, logout_user, login_required

from ..captcha_lib import verify_captcha
from ..html_render import md, allowed_tags, ALLOWED_ATTRIBUTES
from ..decos import permission_required, admin_required
from ..db import DBSession, User, Permission, Forum
from .. import db
from . import points
from .. import captcha_lib
from .. import nongli


@points.route('/punch')
@login_required
def punch():
    k = current_user.punched
    if not current_user.punched:
        current_user.punch()
        current_user.experience += nongli.calculate_punch_points(current_user.punch_days)
        current_user.add_points(nongli.calculate_punch_points(current_user.punch_days), reason='每日签到')

    return render_template(
        'points/punch.html',
        points=nongli.calculate_punch_points(current_user.punch_days),
        next_points=nongli.calculate_punch_points(current_user.punch_days+1),
        k=k
    )


@points.route('/')
@login_required
def points_view():
    return render_template('points/points.html')


@points.route('/records')
@login_required
def records():
    records = current_user.coin_records

    page = request.args.get('page', 1, type=int)
    max_page = math.ceil(records.count() / 25)
    page = min(page, max_page)
    # print(type(records))
    records = records.limit(25).offset((page - 1) * 25).all()
    return render_template('points/records.html', records=records, page=page, max_page=max_page)

