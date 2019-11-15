#!/bin/env python
from setuptools import setup
import subprocess
import os
import sys

setup(
    name='tuber',
    packages=['tuber', 'tuber.models', 'tuber.api'],
    version='0.0.1',
    description="It's a potato.",
    long_description="""Track shifts, sell badges, and more.""",
    license="MIT",
    author='Mark Murnane',
    author_email='mark@hackafe.net',
    url='https://github.com/magfest/tuber',
    keywords=[
        'events',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: No Input/Output (Daemon)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
    ],
    install_requires=[
        'requests',
        'Flask-SQLAlchemy',
        'Flask-Migrate',
        'passlib',
        'flask',
        'gunicorn',
        'psycopg2',
        'flask-talisman',
        'sentry-sdk[flask]',
        'redis',
        'rq',
        'lupa',
        'boto3',
        'jinja2',
        'names',
    ],
    setup_requires=[
        'py2app'
    ],
    app=[
        "tuber/wsgi.py"
    ],
    entry_points={
        'console_scripts': [
            'tuber=tuber.__main__:main',
        ]
    },
)
