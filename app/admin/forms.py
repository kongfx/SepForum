from flask_wtf import FlaskForm as Form
from wtforms import PasswordField, StringField, SubmitField, BooleanField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, EqualTo, Length, AnyOf, Regexp


class UserAdminForm(Form):
    username = StringField('用户名', validators=[DataRequired(), Length(min=1, max=200)])
    password = PasswordField('密码')
    verified = BooleanField('认证')
    perm_read = BooleanField('阅读帖子权限')
    perm_send_post = BooleanField('发帖权限')
    perm_reply = BooleanField('回帖权限')
    perm_moddiscuss = BooleanField('帖子管理')
    redname = BooleanField('红名')
    admin = BooleanField('进入后台/基本管理权限')
    site_admin = BooleanField('超级管理')

    nickname = StringField('昵称')
    badge = StringField('称号')

    banned = BooleanField('封号')
    ban_reason = StringField('封号理由')
    captcha = StringField('验证码', validators=[DataRequired(), Length(min=6, max=6)])

    submit = SubmitField('保存更改')


class PostAdminForm(Form):
    author = IntegerField('发布者 UID', validators=[DataRequired()])
    title = StringField('标题', validators=[DataRequired(), Length(min=1, max=80)])
    content = TextAreaField('HTML 内容')
    content_md = TextAreaField('MD 内容')
    reload_html = BooleanField('重新生成 HTML')
    forum = SelectField('板块')
    banned = BooleanField('是否显示')
    locked = BooleanField('锁定')
    topped = BooleanField('是否置顶（暂时无用）')
    show_author = BooleanField('显示作者')
    captcha = StringField('验证码', validators=[DataRequired(), Length(min=6, max=6)])

    submit = SubmitField('保存更改')


class DenyUserForm(Form):
    reason = StringField('打回/封禁理由', render_kw={'autofocus': 'autofocus'})
    deny = SubmitField('打回')
    ban = SubmitField('封禁', render_kw={'class': 'btn btn-danger'})
