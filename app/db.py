import datetime
import os

from flask import g
from sqlalchemy import Column, String, create_engine, Integer, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.orm import declarative_base
import bcrypt
from flask_login import UserMixin
from . import login_manager

Base = declarative_base()


class Permission:
    READ = 0b1
    SEND_POST = 0b10
    WRITE_COMMENT = 0b100
    MODERATE_DISCUSSION = 0b1000
    RED_NAME = 0b10000
    BACKSTAGE_ENTRANCE = 0b100000
    COIN_MANAGE = 0b1000000
    ADMINISTRATOR = 0b10000000


class Follow(Base):
    __tablename__ = 'follows'
    follower_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    followed_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class User(Base, UserMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)

    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String)
    verified = Column(Boolean, default=False)
    verified_reason = Column(Text)
    perm = Column(Integer, default=0b111)

    nickname = Column(String)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    comments = relationship('Comment', backref='user', lazy='dynamic')
    followed_posts = None
    followed_users = relationship('Follow', backref=backref('follower', lazy='joined'),
                                  foreign_keys='Follow.follower_id')

    followers_users = relationship('Follow', backref=backref('followed', lazy='joined'),
                                   foreign_keys='Follow.followed_id')
    badge = Column(String)
    posts = relationship('Post', backref='author', lazy='dynamic')
    banned = Column(Boolean, default=False)
    ban_reason = Column(String)

    next_changed_name = Column(DateTime, default=datetime.datetime.utcnow)

    slogan = Column(String(150))
    operations = relationship('Operation', backref='user', lazy='dynamic')
    confirmed = Column(Boolean, default=False)
    reg_reason = Column(Text)
    confirm_denied = Column(Boolean, default=False)
    experience = Column(Integer, default=0)
    points = Column(Integer, default=0)
    register_time = Column(DateTime, default=datetime.datetime.utcnow)
    last_punch_date = Column(Date, default=datetime.date(2000, 1, 1))
    punch_days = Column(Integer, default=0)
    coin_records = relationship('CoinRecord', backref='user', lazy='dynamic')
    prize_codes = relationship('PrizeCode', backref='user', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.username == os.environ['FORUM_ADMIN_USER_NAME']:
            self.badge = '吉祥物啦'
            self.perm = 0xffff
            self.nickname = 'TheKo114'
            self.verified = True
            self.confirmed = True

    def change_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash)

    @property
    def is_admin(self):
        return bool(self.perm & Permission.ADMINISTRATOR)

    @property
    def is_ladmin(self):
        return bool(self.perm & Permission.BACKSTAGE_ENTRANCE)

    def has_perm(self, perm):
        return bool(self.perm & perm)

    @property
    def punched(self):
        if datetime.date.today() == self.last_punch_date:
            return True
        return False

    def punch(self):
        if not self.last_punch_date:
            self.last_punch_date = datetime.date(2000, 1, 1)

        no_punch_days = (datetime.date.today() - self.last_punch_date).days - 1
        self.last_punch_date = datetime.date.today()
        if no_punch_days > 0:
            self.punch_days = max(0, self.punch_days - no_punch_days)
        self.punch_days += 1
        g.dbs.add(self)
        g.dbs.commit()

    def add_points(self, points, reason='手动操作'):
        self.points += points
        record = CoinRecord(user_id=self.id, value=points, reason=reason, remainder=self.points)
        g.dbs.add(record)
        g.dbs.commit()


class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String)
    content = Column(Text)
    content_md = Column(Text)
    comments = relationship('Comment', backref='post', lazy='dynamic')
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    hotvalue = Column(Integer)
    forum_id = Column(Integer, ForeignKey('forums.id'), nullable=False)
    banned = Column(Boolean, default=False)
    locked = Column(Boolean, default=False)
    topped = Column(Boolean, default=False)
    show_author = Column(Boolean, default=True)


class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    content = Column(Text)
    content_md = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    hotvalue = Column(Integer)
    banned = Column(Boolean, default=False)
    topped = Column(Boolean, default=False)


class Forum(Base):
    __tablename__ = 'forums'
    id = Column(Integer, primary_key=True)
    show_id = Column(String, unique=True)
    name = Column(String)
    show_in_menus = Column(Boolean, default=True)
    can_post = Column(Boolean, default=True)
    team_id = Column(Integer, ForeignKey('teams.id'))
    description = Column(Text)
    posts = relationship('Post', backref='forum', lazy='dynamic')
    show_author = Column(Boolean, default=True)


class TeamJoinType:
    CANT_JOIN = 1
    NEEDS_REVIEW = 2
    OPEN_JOIN = 3


class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    join_type = Column(Integer, default=TeamJoinType.NEEDS_REVIEW)
    banned = Column(Boolean, default=False)
    forum_id = Column(Integer, ForeignKey('forums.id'), nullable=False)
    members = relationship('TeamMember', backref='team', lazy='dynamic')


class TeamMember(Base):
    __tablename__ = 'team_members'
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_blacklisted = Column(Boolean, default=False)
    nickname = Column(String)
    perm = Column(Integer, default=0b111)
    needs_review = Column(Boolean, default=False)


class ResType:
    USER = 1
    POST = 2
    REPLY = 3
    FORUM = 4
    OTHER = 5


class Operation(Base):
    __tablename__ = 'operations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    endpoint = Column(String)
    res_type = Column(Integer, default=ResType.OTHER)
    url = Column(String)
    ip = Column(String)
    data = Column(Text, default='{"type":"default"}')
    time_used = Column(Integer, default=0)  # unit:ms
    datetime = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(Integer, default=200)


class Captcha(Base):
    __tablename__ = 'captchas'
    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True)
    value = Column(String)


class Prize(Base):
    __tablename__ = 'prizes'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    need_points = Column(Integer)
    description = Column(Text)
    icon_url = Column(String)
    banned = Column(Boolean, default=False)
    codes = relationship('PrizeCode', backref='prize', lazy='dynamic')
    prize_value = Column(Integer)


class PrizeCode(Base):
    __tablename__ = 'prize_codes'
    id = Column(Integer, primary_key=True)
    banned = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    prize_id = Column(Integer, ForeignKey('prizes.id'), nullable=False)
    code = Column(String)
    time = Column(DateTime, default=datetime.datetime.utcnow)
    prize_value = Column(Integer)
    usable_by_other = Column(Boolean, default=False)


class CoinRecord(Base):
    __tablename__ = 'coin_records'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    value = Column(Integer)
    remainder = Column(Integer)
    reason = Column(Text)
    time = Column(DateTime, default=datetime.datetime.utcnow)


engine = create_engine(os.environ.get('DATABASE_URL') or 'sqlite:///data.db')
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
metadata = Base.metadata


# import

@login_manager.user_loader
def load_user(user_id):
    return g.dbs.query(User).filter(User.id == int(user_id)).first()
