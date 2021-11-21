#!/bin/env python
from setuptools import setup

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
        'alembic',
        'passlib',
        'flask>=1.0',
        'gunicorn',
        'redis',
        'lupa',
        'boto3',
        'jinja2',
        'psycopg2-binary',
        'sentry-sdk[flask]'
    ],
    include_package_data=True,
    package_data={
        "tuber": [
            "alembic.ini",
            "migrations/*",
            "migrations/**/*",
            "static/*"
        ]
    },
    app=[
        "tuber/wsgi.py"
    ],
    entry_points={
        'console_scripts': [
            'tuber=tuber.__main__:main',
        ]
    },
)
