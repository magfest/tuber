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
