import json
import math
import time

import bleach
import captcha.image
import datetime

from flask import flash, request, redirect, url_for, g, render_template, abort
from flask_login import current_user, logout_user, login_required

from .forms import UserAdminForm, PostAdminForm, DenyUserForm, GiveUserCoinForm
from ..captcha_lib import verify_captcha
from ..html_render import md, allowed_tags, ALLOWED_ATTRIBUTES
from ..decos import permission_required, admin_required
from ..db import DBSession, User, Permission, Forum
from .. import db
from . import admin
from .. import captcha_lib
from .. import nongli


@admin.route('/')
@permission_required(db.Permission.BACKSTAGE_ENTRANCE)
@login_required
def admin_backstage():
    return render_template('admin/admin_panel.html')


@admin.route('/user/_all')
@admin_required
@login_required
def all_user():
    page = request.args.get('page', 1, type=int)
    max_page = math.ceil(g.dbs.query(db.User).count() / 25)
    page = min(page, max_page)
    users = g.dbs.query(db.User).limit(25).offset((page - 1) * 25).all()
    return render_template("admin/admin_all_user.html", users=users, page=page, max_page=max_page)


@admin.route('/user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
@login_required
def user_admin(user_id):
    form: UserAdminForm = UserAdminForm()
    user = g.dbs.query(db.User).filter(db.User.id == user_id).first()

    if form.validate_on_submit():
        if not verify_captcha(form.captcha.data):
            flash('验证码错误')
            return render_template('admin/user_admin.html', form=form, user=user)

        user.username = form.username.data
        if form.password.data:
            user.change_password(form.password.data)
        user.verified = form.verified.data
        user.perm = (form.perm_send_post.data * db.Permission.SEND_POST |
                     form.perm_read.data * db.Permission.READ |
                     form.perm_reply.data * db.Permission.WRITE_COMMENT |
                     form.perm_moddiscuss.data * db.Permission.MODERATE_DISCUSSION |
                     form.redname.data * db.Permission.RED_NAME |
                     form.admin.data * db.Permission.BACKSTAGE_ENTRANCE |
                     form.site_admin.data * db.Permission.ADMINISTRATOR |
                     form.perm_manage_coin.data * db.Permission.COIN_MANAGE
                     )
        user.nickname = form.nickname.data
        user.badge = form.badge.data
        user.banned = form.banned.data
        user.ban_reason = form.ban_reason.data
        flash('User has been updated.', 'success')
        g.dbs.add(user)
        g.dbs.commit()
        return redirect(url_for('.user_admin', user_id=user.id))
    form.username.data = user.username
    form.password.data = ''
    form.verified.data = user.verified
    form.perm_read.data = user.perm & db.Permission.READ
    form.perm_send_post.data = user.perm & db.Permission.SEND_POST
    form.perm_reply.data = user.perm & db.Permission.WRITE_COMMENT
    form.perm_moddiscuss.data = user.perm & db.Permission.MODERATE_DISCUSSION
    form.redname.data = user.perm & db.Permission.RED_NAME
    form.admin.data = user.perm & db.Permission.BACKSTAGE_ENTRANCE
    form.site_admin.data = user.perm & db.Permission.ADMINISTRATOR
    form.perm_manage_coin.data = user.perm & db.Permission.COIN_MANAGE
    form.nickname.data = user.nickname
    form.badge.data = user.badge
    form.banned.data = user.banned
    form.ban_reason.data = user.ban_reason
    return render_template('admin/user_admin.html', form=form, user=user)

@admin.route('/post/_all')
@permission_required(db.Permission.MODERATE_DISCUSSION)
@login_required
def all_post():
    page = request.args.get('page', 1, type=int)
    max_page = math.ceil(g.dbs.query(db.Post).count() / 25)
    # print(max_page)
    page = min(page, max_page)
    posts = g.dbs.query(db.Post).limit(25).offset((page - 1) * 25).all()
    return render_template("admin/admin_all_posts.html", posts=posts, page=page, max_page=max_page)


@admin.route('/post/<int:post_id>', methods=['GET', 'POST'])
@permission_required(db.Permission.MODERATE_DISCUSSION)
@login_required
def post_admin(post_id):
    form = PostAdminForm()

    forums = g.dbs.query(db.Forum).all()
    post = g.dbs.query(db.Post).filter(db.Post.id == post_id).first()
    form.forum.choices =[(post.forum_id, post.forum.name)]+[(x.id, x.name) for x in forums if x.id != post.forum_id]

    author = post.author
    if post.show_author and not current_user.is_admin:
        abort(404)
    if not post:
        abort(404)
    if form.validate_on_submit():
        if not verify_captcha(form.captcha.data):
            flash('验证码错误')
            return render_template('admin/post_admin.html', post=post, form=form, post_id=post.id)
        if post.author.id != form.author.data:
            new_author = g.dbs.query(db.User).filter(db.User.id == form.author.data).first()
            if not new_author:
                flash('新的作者不存在。', 'danger')
            post.author_id = new_author.id
        post.title = form.title.data
        if current_user.is_admin:
            post.content = form.content.data
        if form.reload_html.data:
            html = md(form.content_md.data)
            cleaned_html = (
                bleach.clean(html, tags=allowed_tags, strip=False, attributes=ALLOWED_ATTRIBUTES))
            post.content = cleaned_html
        post.content_md = form.content_md.data
        post.locked = form.locked.data
        post.topped = form.topped.data
        post.forum_id = form.forum.data
        post.banned = not form.banned.data
        g.dbs.add(post)
        g.dbs.commit()

    form.author.data = post.author_id
    form.title.data = post.title
    form.content.data = post.content
    form.content_md.data = post.content_md
    form.locked.data = post.locked
    form.topped.data = post.topped
    form.reload_html.data = False
    form.forum.data = post.forum_id
    form.banned.data = not post.banned
    return render_template('admin/post_admin.html', post=post, form=form, post_id=post.id)


@admin.route('/user/confirm/')
@login_required
@admin_required
def admin_confirm_user():
    page = request.args.get('page', 1, type=int)
    max_page = math.ceil(g.dbs.query(db.User).count() / 25)
    page = min(page, max_page)
    needs_confirm_user = g.dbs.query(db.User).filter(db.User.confirmed == False).limit(25).offset((page - 1) * 25).all()

    # print(needs_confirm_user)
    return render_template('admin/admin_confirm_user.html', users=needs_confirm_user, page=page, max_page=max_page)


@admin.route('/user/confirm/<int:user_id>/')
@login_required
@admin_required
def admin_confirm_user_op(user_id):
    user = g.dbs.query(db.User).filter(db.User.id == user_id).first()
    if user is None or user.confirmed:
        abort(404)
    return render_template('admin/admin_confirm_user_op.html', user=user)

@admin.route('/user/confirm/<int:user_id>/pass/')
@login_required
@admin_required
def admin_confirm_user_op_pass(user_id):
    user = g.dbs.query(db.User).filter(db.User.id == user_id).first()
    if user is None or user.confirmed:
        abort(404)
    user.confirmed = True
    user.confirm_denied = False
    g.dbs.add(user)
    g.dbs.commit()
    next_user = g.dbs.query(db.User).filter(db.User.confirmed == False, db.User.confirm_denied == False).first()
    flash(f'用户 {user.username} 已通过。', 'success')
    if next_user is None:
        return redirect(url_for('.admin_confirm_user'))
    else:
        return redirect(url_for('.admin_confirm_user_op', user_id=next_user.id))


@admin.route('/user/confirm/<int:user_id>/deny/', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_confirm_user_op_deny(user_id):
    user = g.dbs.query(db.User).filter(db.User.id == user_id).first()
    if user is None or user.confirmed:
        abort(404)
    form = DenyUserForm()
    if form.validate_on_submit():
        if form.deny.data:
            # print('deny')
            user.confirm_denied = True
            user.confirmed = False
            user.ban_reason = form.reason.data
            flash(f'用户 {user.username} 已打回。', 'success')
        elif form.ban.data:
            # print('ban')
            user.ban_reason = form.reason.data
            user.banned = True
            flash(f'用户 {user.username} 已封禁。', 'success')
        g.dbs.add(user)
        g.dbs.commit()
        next_user = g.dbs.query(db.User).filter(db.User.confirmed == False, db.User.confirm_denied == False).first()
        if next_user is None:
            return redirect(url_for('.admin_confirm_user'))
        else:
            return redirect(url_for('.admin_confirm_user_op', user_id=next_user.id))
    return render_template('admin/admin_confirm_user_op_deny.html', user=user, form=form)


@admin.route('/captcha/clear')
@login_required
@admin_required
def clear_captcha():
    num = g.dbs.query(db.Captcha).delete()
    g.dbs.commit()
    return f'DELETE DONE; deleted {num} rows'

@admin.route('/coin/records')
@login_required
@permission_required(Permission.COIN_MANAGE)
def coin_records():
    user_id = request.args.get('user', None)
    if user_id is not None:
        user = g.dbs.query(db.User).filter(db.User.id == user_id).first()
        if not user:
            abort(404)
        records = user.coin_records
    else:
        records = g.dbs.query(db.CoinRecord)
    page = request.args.get('page', 1, type=int)
    max_page = math.ceil(records.count() / 25)
    page = min(page, max_page)
    records = records.limit(25).offset((page - 1) * 25).all()
    return render_template('admin/coin_records.html', records=records, page=page, max_page=max_page)


@admin.route('/coin/give', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.COIN_MANAGE)
def give_coin():
    form = GiveUserCoinForm()
    if form.validate_on_submit():
        user = g.dbs.query(User).filter(User.id==form.user_id.data).first()
        if not user:
            flash('未找到用户。', 'error')
            return redirect(url_for('.give_coin'))
        if user.points + form.value.data < 0:
            flash('用户余额不能为负数。', 'error')
            return redirect(url_for('.give_coin'))
        user.add_points(form.value.data, f'管理员 @{current_user.username} 操作；{form.reason.data}')
        flash('操作成功。', 'success')
        return redirect(url_for('.coin_records'))
    return render_template('admin/give_coin.html', form=form)

