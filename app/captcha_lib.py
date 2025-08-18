import datetime
import random
import string

from flask import g, session
from . import db



def get_captcha_str():
    try:
        return g.dbs.query(db.Captcha).filter(db.Captcha.token == session['captcha_token']).first().value
    except:
        # 谁会反复提交同一个验证码token啊！！！！！！！
        return ''


def verify_captcha(c):
    try:
        return c.strip().lower() == get_captcha_str().lower()
    except KeyError:
        return False


def generate_captcha():
    chars = set(string.ascii_letters + string.digits) - {'I', 'l', '0', 'O'}
    captcha_str = ''.join(random.choice(list(chars)) for _ in range(6))
    token = int(str(random.randint(10000000, 999999999)) +
                str(datetime.datetime.now().timestamp()).replace('.', '')) ^ 0xCAFEDDAEA
    session['captcha_token'] = str(token)
    cpc = db.Captcha(token=str(token), value=captcha_str)
    g.dbs.add(cpc)
    g.dbs.commit()
    return captcha_str