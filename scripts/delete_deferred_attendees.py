from secrets import TUBER_URL, TUBER_APIKEY, TUBER_EVENT
import uber_api
import requests
import json

attendees = uber_api.get_eligible_attendees()

headers = {
    "X-Auth-Token": TUBER_APIKEY
}

to_delete = []

for attendee_id in attendees:
    attendee = uber_api.get_attendee(attendee_id)
    if attendee['badge_status_label'] == "Deferred":
        print(attendee['full_name'])
        request = requests.get(f'{TUBER_URL}/api/event/{TUBER_EVENT}/badge?uber_id={attendee_id}', headers=headers)
        results = json.loads(request.text.strip())
        assert len(results) <= 1
        if len(results) == 1:
            to_delete.append(results[0])

for badge in to_delete:
    print(badge['id'], badge['public_name'])
    request = requests.delete(f"{TUBER_URL}/api/event/{TUBER_EVENT}/badge/{badge['id']}", headers=headers)
    print(f"{request.status_code}: {request.text.strip()}")