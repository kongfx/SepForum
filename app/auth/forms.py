from flask_wtf import FlaskForm as Form
from wtforms import PasswordField, StringField, SubmitField, BooleanField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, EqualTo, Length, AnyOf


class LoginForm(Form):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    captcha = StringField('验证码', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('登录')

class RegistrationForm(Form):
    username = StringField('用户名', validators=[DataRequired(), Length(min=4, max=20)])
    # verify_code = StringField('邀请码', validators=[DataRequired(), Length(min=6, max=6)])
    password = PasswordField('密码', validators=[DataRequired()])
    password2 = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    terms_read = BooleanField('同意用户协议（见下）',validators=[DataRequired(), AnyOf([True], '请同意用户协议')])
    captcha = StringField('验证码', validators=[DataRequired(), Length(min=6, max=6)])
    reg_reason = StringField('注册信息（包含理由、身份，以及电子邮箱或手机号，最多 400 字）', validators=[DataRequired(), Length(min=10, max=400)])
    submit = SubmitField('注册')


class ChangePasswordForm(Form):
    old_password = PasswordField('旧密码', validators=[DataRequired()])
    password = PasswordField('新密码', validators=[DataRequired()])
    password2 = PasswordField('确认新密码', validators=[DataRequired(), EqualTo('password')])
    captcha = StringField('验证码', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('确认修改')

class ReSendRequestForm(Form):
    reg_reason = StringField('重新填写信息（包含理由、身份，以及电子邮箱或手机号，最多 400 字）',
                             validators=[DataRequired(), Length(min=10, max=400)])
    captcha = StringField('验证码', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('确认提交')
