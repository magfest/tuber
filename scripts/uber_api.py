from secrets import UBER_API_KEY, UBER_URL
import requests

headers = {
    "X-Auth-Token": UBER_API_KEY
}

def get_eligible_attendees():
    req = {
        "method": "hotel.eligible_attendees"
    }
    return requests.post(UBER_URL, headers=headers, json=req).json()['result']

def get_attendee(uber_id, full=False):
    req = {
        "method": "attendee.search",
        "params": [
            uber_id
        ]
    }
    if full:
        req['params'].append("full")
    return requests.post(UBER_URL, headers=headers, json=req).json()['result'][0]