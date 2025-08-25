from flask_wtf import FlaskForm as Form
from wtforms import PasswordField, StringField, SubmitField, BooleanField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, EqualTo, Length, AnyOf

class TransferForm(Form):
    user = StringField('用户名/用户 ID', validators=[DataRequired()])
    value = IntegerField('金额',validators=[DataRequired()])
    reason = StringField('缘由', validators=[DataRequired(), Length(min=1, max=50)])
    password = PasswordField('密码', validators=[DataRequired()])
    captcha = StringField('验证码', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('确认转账')