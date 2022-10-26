"""The base module for Tuber"""

import os
from flask import Flask
from tuber import config

app = Flask(__name__)

import tuber.csrf
import tuber.models
import tuber.api
import tuber.aws
