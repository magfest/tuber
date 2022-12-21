from secrets import TUBER_URL, TUBER_APIKEY, TUBER_EVENT
import uber_api
import requests
import json
import sys
import os

headers = {
    "X-Auth-Token": TUBER_APIKEY
}

BASE_URL = f'{TUBER_URL}/api/event/{TUBER_EVENT}'


def get(url, as_dict=False, refresh=False):
    path = os.path.join("cache", url.replace("/", "_")+".json")
    if os.path.isfile(path) and not refresh:
        with open(path, "r") as FILE:
            data = json.loads(FILE.read())
    else:
        data = requests.get(url, headers=headers).json()
        with open(path, "w") as FILE:
            FILE.write(json.dumps(data))
    if as_dict:
        return {x['id']: x for x in data}
    return data


room_nights = get(f"{BASE_URL}/hotel_room_night")
uber_room_nights = uber_api.get_nights()
room_nights_lookup = {}
for room_night in room_nights:
    if room_night['date'] in uber_room_nights.keys():
        room_nights_lookup[room_night['id']
                           ] = uber_room_nights[room_night['date']]
    # else:
        #print(f"Could not find uber entry for {room_night['name']}")
# print(room_nights_lookup)

rooms = get(f"{BASE_URL}/hotel_room")
assignments = get(f"{BASE_URL}/room_night_assignment")
badges = get(f"{BASE_URL}/badge")
badges = {x['id']: x for x in badges}
hrr = get(f"{BASE_URL}/hotel_room_request?full=true&deep=true")
hrr = {x['badge']: x for x in hrr}
reqs = {}
# print(json.dumps(hrr[0]))

for room in rooms:
    nights = []
    assign = []
    assigned = []
    for ass in assignments:
        if ass['hotel_room'] == room['id']:
            assign.append(ass)
    for ass in assign:
        if not ass['room_night'] in nights:
            nights.append(ass['room_night'])
    ubernights = [room_nights_lookup[x]
                  for x in nights if x in room_nights_lookup]
    room = uber_api.create_room(
        notes=room['notes'],
        message=room['messages'],
        locked_in=room['completed'],
        nights=ubernights
    )
    print(room)
    for ass in assign:
        badge = ass['badge']
        if not badge in reqs.keys():
            req = hrr[badge]
            reqs[badge] = req
            requested_nights = [x['room_night']
                                for x in req["room_night_requests"] if x['requested']]
            req_nights = [room_nights_lookup[x]
                          for x in nights if x in room_nights_lookup and x in requested_nights]
            request = uber_api.create_request(
                attendee_id=badges[badge]['uber_id'],
                special_needs=hrr[badge]['notes'],
                approved=True,
                nights=req_nights
            )
            print(request)
        if not badge in assigned:
            assigned.append(badge)
            try:
                assignment = uber_api.assign_roommate(
                    room_id=room['id'],
                    attendee_id=badges[badge]['uber_id']
                )
                print(assignment)
            except:
                print(
                    f"Failed to assign roommate {badges[badge]['uber_id']} ({badges[badge]['search_name']})")
