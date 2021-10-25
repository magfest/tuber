"""The base module for Tuber"""

from flask import Flask
from flask_talisman import Talisman
from tuber import config

app = Flask(__name__)

if config.flask_env == "production":
    csp = config.csp_directives
    if not csp:
        csp = {
            'default-src': '\'self\'',
            'style-src': [
                '\'unsafe-inline\' \'self\'',
                'fonts.googleapis.com',
                'use.fontawesome.com',
            ],
            'font-src': [
                'fonts.gstatic.com',
                'use.fontawesome.com',
            ],
            'worker-src': [
                'blob:',
            ],
            'img-src': [
                'https:',
            ],
        }
        
    if config.force_https:
        talisman = Talisman(app, content_security_policy=csp)

import tuber.csrf
import tuber.models
import tuber.api
