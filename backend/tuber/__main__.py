import argparse
import tuber
import json
import sys
import os

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Increase Verbosity", action="store_true")
parser.add_argument("-e", "--flask_env", help="Set the flask environment")
parser.add_argument("-s", "--static_path", help="Set the folder to serve static files from")
parser.add_argument("-m", "--migrations_path", help="Set the folder that contains the sql database migrations to run")
parser.add_argument("-d", "--database_url", help="Set the connection string for the sql server")
parser.add_argument("-S", "--session_duration", help="Sets the duration of a user session", type=int)
parser.add_argument("-u", "--uber_api_token", help="The API key to use when importing data from uber")
parser.add_argument("-U", "--uber_api_url", help="The URL of the uber server to import data from")
parser.add_argument("-c", "--config", help="Path to the tuber config file")

def main():
    args = parser.parse_args()
    configfile = {}
    if args.config and os.path.isfile(args.config):
        with open(args.config, "r") as FILE:
            configfile = json.loads(FILE.read())

    for i in vars(args).keys():
        if getattr(args, i):
            configfile[i] = getattr(args, i)
    for i in configfile:
        setattr(tuber.config, i, configfile[i])

    tuber.migrate()
    tuber.app.run(host='0.0.0.0', port=8080)
