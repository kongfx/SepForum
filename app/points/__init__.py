from flask import Blueprint

points = Blueprint('points', __name__)

from . import views
