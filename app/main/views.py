import base64
import json
import math
import os
import sys
import time

import bleach
import captcha.image
import datetime

from flask import flash, request, redirect, url_for, g, render_template, abort, Response
from flask_login import current_user, logout_user, login_required

from ..captcha_lib import verify_captcha
from ..html_render import md, allowed_tags, ALLOWED_ATTRIBUTES
from .forms import NewPostForm, NewReplyForm
from ..decos import permission_required, admin_required
from ..db import DBSession, User, Permission, Forum
from .. import db
from . import main
from .. import captcha_lib
from .. import nongli

captcha_fn = captcha.image.ImageCaptcha(width=180)
POST_PER_PAGE = 20
REPLY_PER_PAGE = 25
day_sk = '5LuK5aSp5piv4oCc5LmdwrfkuIDlhavkuovlj5jigJ17fSDlkajlubTjgILlnKjmraTnuqrlv7XkuLrlm73nibrnibLnmoTng4jlo6vku6zvvIzmsLjlnoLkuI3mnL3vvIEK'

@main.app_context_processor
def context_processor():
    today = datetime.date.today()
    y,m,d = nongli.get_nongli(today)
    red_theme = m==1 and d in range(1,8) or os.environ['FORCE_RED_THEME']=='true'
    grayscale = (today.month==9 and today.day == 18) or os.environ['FORCE_GRAYSCALE']=='true'
    return dict(timestamp=datetime.datetime.now().timestamp(), Permission=db.Permission, FORUM_NAME=os.environ.get('FORUM_NAME', '论坛'), red_theme=red_theme, grayscale=grayscale)


@main.before_app_request
def before_request():
    g.dbs = DBSession()
    # print(request.path)
    if current_user.is_authenticated and current_user.banned and current_user.perm & db.Permission.ADMINISTRATOR == 0:
        flash(f'封禁用户，申诉微信/线下联系。你已被登出。理由：' + current_user.ban_reason)
        logout_user()
    if current_user.is_authenticated and not current_user.confirmed and (
            request.endpoint != "static") and not request.path.startswith(
        "/auth") and request.endpoint != 'main.gen_captcha':
        # flash("")
        return redirect(url_for('auth.unconfirmed'))

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


@main.teardown_app_request
def after_request(response):
    if current_user.is_authenticated and request.endpoint != "auth.login":
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


@main.route('/captcha/')
def gen_captcha():
    return Response(captcha_fn.generate(captcha_lib.generate_captcha()), mimetype="image/png")


@main.route('/')
def index():
    day, weeknum, nongli_, jieqi, today = nongli.nongli(datetime.date.today())
    today = datetime.date.today()
    y, m, d = nongli.get_nongli(today)
    red_theme = m == 1 and d in range(1, 8) or os.environ['FORCE_RED_THEME'] == 'true'
    grayscale = (today.month == 9 and today.day == 18) or os.environ['FORCE_GRAYSCALE'] == 'true'
    return render_template('index.html',
                           day=day, weeknum=weeknum, nongli=nongli_, jieqi=jieqi, today=today, red_theme=red_theme, grayscale=grayscale, sp_msg=base64.b64decode(day_sk).decode('utf-8').format(y-1931))


@main.route('/user/<int:user_id>/')
@login_required
def user(user_id):
    user = g.dbs.query(User).filter(User.id == user_id).first()
    if user is None:
        abort(404)
    return render_template('user.html', user=user)


@main.route('/forum/_all/')
@login_required
@permission_required(Permission.READ)
def forum_all():
    if current_user.perm & Permission.MODERATE_DISCUSSION:
        forums = g.dbs.query(Forum).all()
    else:
        forums = g.dbs.query(Forum).filter(Forum.show_in_menus == True).all()
    return render_template('all_forum.html', forums=forums)


@main.route('/forum/<int:forum_id>/')
@permission_required(db.Permission.READ)
@login_required
def forum(forum_id):
    page = request.args.get('page', 1, int)
    posts = (g.dbs.query(db.Post)
             .filter(db.Post.banned == False)
             .filter(db.Post.forum_id == forum_id)
             .order_by(db.Post.timestamp.desc())
             .limit(POST_PER_PAGE)
             .offset(POST_PER_PAGE * (page - 1))
             .all()
             )
    post_count = (g.dbs.query(db.Post).filter(db.Post.banned == False)
                  .filter(db.Post.forum_id == forum_id)
                  .count()
                  )
    max_page = math.ceil(post_count / POST_PER_PAGE)
    forum = g.dbs.query(db.Forum).filter(db.Forum.id == forum_id).first()
    if forum is None:
        abort(404)
    return render_template('forum_post.html', posts=posts,
                           page=page,
                           max_page=max_page,
                           post_count=post_count,
                           forum=forum
                           )


@main.route('/post/_new/', methods=['GET', 'POST'])
@login_required
def new_post():
    if not current_user.has_perm(Permission.SEND_POST):
        abort(404)
    form = NewPostForm()
    if current_user.perm & Permission.MODERATE_DISCUSSION:
        forums = g.dbs.query(Forum).all()
    else:
        forums = g.dbs.query(Forum).filter(Forum.show_in_menus == True).all()
    form.forum.choices = [(x.id, x.name) for x in forums]
    if form.validate_on_submit():
        if not verify_captcha(form.captcha.data):
            flash('验证码错误')
            return render_template("new_post.html", form=form)
        if len(form.content.data) > 5000 and current_user.perm & db.Permission.BACKSTAGE_ENTRANCE == 0:
            flash('帖子太长了', 'danger')
            return render_template('new_post.html', form=form)
        html = md(form.content.data)
        cleaned_html = (bleach.clean(html, tags=allowed_tags, strip=False, attributes=ALLOWED_ATTRIBUTES))
        forum: db.Forum = g.dbs.query(db.Forum).get(form.forum.data)

        post = db.Post(title=form.title.data, content=cleaned_html, author_id=current_user.id,
                       content_md=form.content.data, forum_id=form.forum.data, show_author=not forum.show_author)
        g.dbs.add(post)
        g.dbs.commit()
        return redirect(url_for('.post', post_id=post.id))
    return render_template("new_post.html", form=form)


@main.route('/post/<int:post_id>/', methods=['GET', 'POST'])
@permission_required(Permission.READ)
@login_required
def post(post_id):

    post = g.dbs.query(db.Post).filter(db.Post.id == post_id).first()
    if post is None:
        abort(404)

    if post.banned and not current_user.is_ladmin:
        abort(404)
    author = g.dbs.query(User).filter(User.id == post.author_id).first()
    canban = current_user.perm & db.Permission.MODERATE_DISCUSSION or current_user == author
    page = request.args.get('page', 1, type=int)
    if current_user.perm & db.Permission.MODERATE_DISCUSSION:
        lor = post.comments.count()
    else:
        lor = post.comments.filter(db.Comment.banned == False).count()
    max_page = math.ceil(post.comments.count() / POST_PER_PAGE)
    page = min(max_page, page)
    replies = (post.comments
               .order_by(db.Comment.timestamp.asc())
               .limit(REPLY_PER_PAGE)
               .offset((page - 1) * REPLY_PER_PAGE))

    form = NewReplyForm()
    if form.validate_on_submit():
        if not verify_captcha(form.captcha.data):
            flash('验证码错误')
            return render_template("apost.html", post=post, author=author, canban=canban, form=form,
                                   replies=replies.all(), lor=lor,
                                   show_form=not (
                                           post.locked and current_user.perm & db.Permission.BACKSTAGE_ENTRANCE == 0),
                                   show_banned_reply=bool(current_user.perm & db.Permission.MODERATE_DISCUSSION),
                                   page=page,
                                   max_page=max_page,
                                   show_name=True
                                   )
        if current_user.perm & db.Permission.WRITE_COMMENT == 0:
            flash('Permission Denied')
            return redirect(url_for('post', post_id=post.id))
        if len(form.content.data) > 1000 and current_user.perm & db.Permission.BACKSTAGE_ENTRANCE == 0:
            flash('回帖太长了', 'danger')
            return render_template("apost.html", post=post, author=author, canban=canban)
        if post.locked and current_user.perm & db.Permission.BACKSTAGE_ENTRANCE == 0:
            flash('帖子已锁定')
            return render_template("apost.html", post=post, author=author, canban=canban)
        html = md(form.content.data)
        cleaned_html = (bleach.clean(html, tags=allowed_tags, strip=False, attributes=ALLOWED_ATTRIBUTES))
        cmt = db.Comment(author_id=current_user.id, post_id=post.id, content=cleaned_html, content_md=form.content.data)
        g.dbs.add(cmt)
        g.dbs.commit()
        return redirect(url_for('.post', post_id=post.id))
    return render_template("apost.html", post=post, author=author, canban=canban, form=form,
                           replies=replies.all(), lor=lor,
                           show_form=not (post.locked and current_user.perm & db.Permission.BACKSTAGE_ENTRANCE == 0),
                           show_banned_reply=bool(current_user.perm & db.Permission.MODERATE_DISCUSSION),
                           page=page,
                           max_page=max_page,
                           show_name=not post.show_author
                           )


@main.route('/r/<int:reply_id>')
def reply(reply_id):
    reply = g.dbs.query(db.Comment).filter(db.Comment.id == reply_id).first()
    return render_template("reply.html", reply=reply)


@main.route('/favicon.ico/')
def favicon():
    return redirect('/static/favicon.ico')

@main.route('/captcha/fun/', methods=['GET', 'POST'])
def captcha_fun():
    message = '猜一猜验证码吧！'
    form = forms.CaptchaFun()
    if form.validate_on_submit():
        try:
            if verify_captcha(form.captcha.data):
                message = '恭喜你，猜对了！验证码是 ' + get_captcha_str()
            else:
                message = '很遗憾，猜错了，答案是 ' + get_captcha_str()
        except:
            # tmd 多线程获取不了
            message = '很遗憾，猜错了，答案未知（服务器经过重启）'
            print(sys.exc_info(), file=sys.stderr)
            raise
    return render_template('captcha_test.html', form=form, message=message)