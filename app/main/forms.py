from flask_wtf import FlaskForm as Form
from wtforms import PasswordField, StringField, SubmitField, BooleanField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, EqualTo, Length, AnyOf

class NewPostForm(Form):
    forum = SelectField('发布版面')
    title = StringField('标题', validators=[DataRequired(),Length(min=4, max=25)])
    content = TextAreaField('内容（最多 16384 字）', validators=[DataRequired(),Length(min=5, max=40960)])
    captcha = StringField('验证码', validators=[DataRequired(), Length(min=6, max=6)])

    submit = SubmitField('提交')

class NewReplyForm(Form):
    content = TextAreaField('回帖内容', validators=[DataRequired(), Length(min=2, max=16384)])
    captcha = StringField('验证码', validators=[DataRequired(), Length(min=6, max=6)])

    submit = SubmitField('提交')

class EditPostForm(Form):
    title = StringField('标题', validators=[DataRequired(), Length(min=4, max=25)])
    content = TextAreaField('内容', validators=[DataRequired(), Length(min=4, max=8192)])
    captcha = StringField('验证码', validators=[DataRequired(), Length(min=6, max=6)])

    submit = SubmitField('提交')


class OperationsControlForm(Form):
    user = IntegerField('UID', validators=[DataRequired()])
    page = IntegerField('页码', default=1, validators=[DataRequired()])
    captcha = StringField('验证码', validators=[DataRequired(), Length(min=6, max=6)])

    submit = SubmitField('提交')


class AnonymousPostEditForm(Form):
    title = StringField('标题', validators=[DataRequired(), Length(min=4, max=25)])
    content = TextAreaField('内容', validators=[DataRequired(), Length(min=4, max=8192)])
    captcha = StringField('验证码', validators=[DataRequired(), Length(min=6, max=6)])

    # is_anonymous = BooleanField('是否隐藏你的名字（注意：取消后不可改回！）')
    submit = SubmitField('提交')