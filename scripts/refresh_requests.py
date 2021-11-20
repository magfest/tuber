from secrets import TUBER_URL, TUBER_APIKEY, TUBER_EVENT
from types import SimpleNamespace
import itertools
import datetime
import uber_api
import requests
import json
import sys
import os

headers = {
    "X-Auth-Token": TUBER_APIKEY
}

BASE_URL = f'{TUBER_URL}/api/event/{TUBER_EVENT}'

req = requests.post(f"{BASE_URL}/hotel/update_requests", headers=headers)
print(req.status_code)
print(json.dumps(req.json(), indent=2))