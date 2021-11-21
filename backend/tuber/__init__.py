"""The base module for Tuber"""

from os import environ
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flask import Flask
from tuber import config

if 'SENTRY_DSN' in os.environ:
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[FlaskIntegration()],

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0
    )

app = Flask(__name__)

import tuber.csrf
import tuber.models
import tuber.api
