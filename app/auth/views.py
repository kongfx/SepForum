from flask import flash, render_template, g, url_for, request, redirect
from flask_login import login_user, login_required, logout_user, current_user

from ..captcha_lib import verify_captcha
from ..db import User
from . import auth
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, ReSendRequestForm


@auth.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if not verify_captcha(form.captcha.data):
            flash('验证码错误')
            return render_template('auth/login.html', form=form)
        user = g.dbs.query(User).filter(User.username == form.username.data).first()
        if not user:
            form.password.errors.append('用户名或密码错误')
            return render_template('auth/login.html', form=form)
        if not user.check_password(form.password.data):
            form.password.errors.append('用户名或密码错误')
            return render_template('auth/login.html', form=form)
        if login_user(user, remember=form.remember_me.data):
            next = request.args.get('next')
            flash(f'登录成功。', 'info')
            return redirect(next or url_for('main.index'))
        flash(f'未知错误。', 'error')

    return render_template('auth/login.html', form=form)

@auth.route('/register/', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if not verify_captcha(form.captcha.data):
            flash('验证码错误')
            return render_template('auth/register.html', form=form)

        if g.dbs.query(User).filter(User.username == form.username.data).first() is None:
            user = User(username=form.username.data, reg_reason=form.reg_reason.data)
            user.change_password(form.password.data)
            flash(f'注册成功。请登录。', 'success')
            g.dbs.add(user)
            g.dbs.commit()
            return redirect(url_for('.login'))
        flash(f'用户名重复。', 'error')
        return render_template('auth/register.html', form=form)
    return render_template('auth/register.html', form=form)


@auth.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('你已被登出。', 'info')
    return redirect(url_for('main.index'))

@auth.route('/change_password/', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if verify_captcha(form.captcha.data):
            if current_user.check_password(form.old_password.data):
                current_user.change_password(form.password.data)
                flash('修改成功。', 'success')
            else:
                flash('旧密码错误。', 'danger')
        else:
            flash('验证码错误', 'danger')
    return render_template('auth/change_password.html', form=form)

@auth.route('/unconfirmed/', methods=['GET'])
@login_required
def unconfirmed():
    if current_user.confirmed:
        flash('你的账号已通过审核，欢迎！')
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

@auth.route('/unconfirmed/re-send/', methods=['GET', 'POST'])
@login_required
def re_send_req():
    if current_user.confirmed or not current_user.confirm_denied:
        return redirect(url_for('main_page'))
    form = ReSendRequestForm()
    if form.validate_on_submit():
        if not verify_captcha(form.captcha.data):
            flash('验证码错误。')
            return render_template('auth/resend_req.html', form=form)
        current_user.reg_reason = '【用户请求重审】' + form.reg_reason.data
        current_user.confirm_denied = False
        g.dbs.add(current_user._get_current_object())
        g.dbs.commit()
        flash('重审申请成功！', 'success')
        return redirect(url_for('.unconfirmed'))
    return render_template('auth/resend_req.html', form=form)

