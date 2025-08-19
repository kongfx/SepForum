import os

import json

from app import create_app

conf = json.load(open('config.json'))

os.environ.update(conf)

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
