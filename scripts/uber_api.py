from secrets import UBER_API_KEY, UBER_URL
import requests
import datetime
import csv
import os

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


def create_room(notes="", message="", locked_in="", nights=None):
    req = {
        "method": "hotel.update_room",
        "params": {
            "notes": notes,
            "message": message,
            "locked_in": locked_in
        }
    }
    if nights != None:
        req['params']['nights'] = ",".join(nights)
    res = requests.post(UBER_URL, headers=headers, json=req).json()
    return res['result']


existing_requests = {}
if os.path.isfile("HotelRequests.csv"):
    with open("HotelRequests.csv", "r", encoding="utf-8") as FILE:
        reader = csv.DictReader(FILE, delimiter=",")
        for record in reader:
            existing_requests[record['attendee_id']] = record['id']


def create_request(id=None, attendee_id="", nights=None, wanted_roommates="", unwanted_roommates="", special_needs="", approved=True):
    req = {
        "method": "hotel.update_request",
        "params": {
            "attendee_id": attendee_id,
            "wanted_roommates": wanted_roommates,
            "unwanted_roommates": unwanted_roommates,
            "special_needs": special_needs,
            "approved": approved
        }
    }
    if attendee_id in existing_requests:
        req['params']['id'] = existing_requests[attendee_id]
    if id != None:
        req['params']['id'] = id
    if nights != None:
        req['params']['nights'] = ",".join(nights)
    res = requests.post(UBER_URL, headers=headers, json=req).json()
    print(res)
    return res


def assign_roommate(room_id="", attendee_id=""):
    req = {
        "method": "hotel.update_assignment",
        "params": {
            "attendee_id": attendee_id,
            "room_id": room_id
        }
    }
    return requests.post(UBER_URL, headers=headers, json=req).json()['result']


def get_nights():
    req = {
        "method": "hotel.nights"
    }
    result = requests.post(UBER_URL, headers=headers,
                           json=req).json()['result']
    dates = {key.lower(): value for key, value in result['dates'].items()}
    lookup = {}
    for idx, name in enumerate(result['names']):
        if not name in dates:
            continue
        newdate = datetime.datetime.strptime(
            dates[name], "%Y-%m-%d") + datetime.timedelta(days=1)
        newdate = newdate.strftime("%Y-%m-%d")
        lookup[newdate] = str(result['order'][idx])
    return lookup

def get_departments():
    req = {
        "method": "dept.list"
    }
    return requests.post(UBER_URL, headers=headers, json=req).json()['result']

def get_shifts():
    departments = get_departments()
    shifts = {}
    for dept_id, dept_name in departments.items():
        print(f"Loading shifts from {dept_name}")
        req = {
            "method": "shifts.lookup",
            "params": {
                "department_id": dept_id
            }
        }
        shifts[dept_id] = requests.post(UBER_URL, headers=headers, json=req).json()['result']
        print(f"  Got {len(shifts[dept_id])} shifts")
    return shifts
