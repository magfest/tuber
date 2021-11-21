"""The base module for Tuber"""

from flask import Flask
from tuber import config

app = Flask(__name__)

import tuber.csrf
import tuber.models
import tuber.api
