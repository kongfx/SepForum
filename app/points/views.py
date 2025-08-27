import json
import math
import time
import uuid

import bleach
import captcha.image
import datetime

from flask import flash, request, redirect, url_for, g, render_template, abort
from flask_login import current_user, logout_user, login_required

from .forms import TransferForm, BuyCheckForm, RedeemForm
from ..captcha_lib import verify_captcha
from ..html_render import md, allowed_tags, ALLOWED_ATTRIBUTES
from ..decos import permission_required, admin_required
from ..db import DBSession, User, Permission, Forum, PrizeCode
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


@points.route('transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    form = TransferForm()
    if form.validate_on_submit():
        if not verify_captcha(form.captcha.data):
            form.captcha.errors.append('验证码错误')
            return render_template('points/transfer.html', form=form)
        if not current_user.check_password(form.password.data):
            form.password.errors.append('密码错误')
            return render_template('points/transfer.html', form=form)
        if form.value.data <= 0:
            form.value.errors.append('金额必须大于 0')
            return render_template('points/transfer.html', form=form)
        if current_user.points < form.value.data:
            form.value.errors.append('余额不足')
            return render_template('points/transfer.html', form=form)
        if form.user.data.isdigit():
            user = g.dbs.query(User).get(int(form.user.data))
        else:
            user = g.dbs.query(User).filter(User.username == form.user.data).first()
        if not user:
            form.user.errors.append('用户不存在。')
            return render_template('points/transfer.html', form=form)
        if user.banned:
            form.user.errors.append('用户被封禁。')
            return render_template('points/transfer.html', form=form)
        current_user.add_points(-form.value.data, f'转账给 @{user.username}。缘由：{form.reason.data}')
        user.add_points(form.value.data, f'转账来自 @{current_user.username}。缘由：{form.reason.data}')
        g.dbs.add(user)
        g.dbs.add(current_user._get_current_object())
        g.dbs.commit()
        flash(f'转账成功。给 @{user.username} 转账了 {form.value.data} 金币。余额 {current_user.points} 金币。', 'success')
        return redirect(url_for('points.points_view'))
    return render_template('points/transfer.html', form=form)


@points.route('/shop/')
@login_required
def shop():
    prizes = g.dbs.query(db.Prize)

    page = request.args.get('page', 1, type=int)
    max_page = math.ceil(prizes.count() / 25)
    page = min(page, max_page)
    # print(type(records))
    prizes = prizes.limit(25).offset((page - 1) * 25).all()
    return render_template('points/shop.html', prizes=prizes, page=page, max_page=max_page)


@points.route('/buy/<int:prize_id>', methods=['GET', 'POST'])
@login_required
def buy(prize_id):
    prize = g.dbs.query(db.Prize).get(prize_id)
    if not prize:
        abort(404)
    form = BuyCheckForm()
    if form.validate_on_submit():
        print(1)
        current_user.add_points(-prize.need_points, f'购买商品 "{prize.name}"#{prize.id}，{"" if form.usable_by_other.data else "不"}可被他人使用。')
        prize_code = PrizeCode(user_id=current_user.id, code=str(uuid.uuid4()), prize_value=prize.prize_value, usable_by_other=form.usable_by_other.data, prize_id=prize.id)
        g.dbs.add(prize_code)
        g.dbs.add(current_user._get_current_object())
        g.dbs.commit()
        return redirect(url_for('points.order', order_id=prize_code.id))
    return render_template('points/buy.html', prize=prize, form=form)


@points.route('/order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def order(order_id):
    order = g.dbs.query(db.PrizeCode).get(order_id)
    if not order:
        abort(404)
    if order.user_id != current_user.id:
        abort(404)
    return render_template('points/buy_success.html', ps=order)


@points.route('/order/list')
@login_required
def order_list():
    orders = current_user.prize_codes

    page = request.args.get('page', 1, type=int)
    max_page = math.ceil(orders.count() / 25)
    page = min(page, max_page)
    # print(type(records))
    orders = orders.limit(25).offset((page - 1) * 25).all()
    return render_template('points/order_list.html', orders=orders, page=page, max_page=max_page)

#
# @points.route('/redeem/', methods=['GET', 'POST'])
# @login_required
# def redeem():
#     form = RedeemForm()
#     if form.validate_on_submit():
#         order = g.dbs.query(db.PrizeCode).filter()