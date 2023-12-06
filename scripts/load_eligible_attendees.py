from secrets import TUBER_URL, TUBER_APIKEY
import uber_api
import requests

headers = {
    "X-Auth-Token": TUBER_APIKEY
}

#attendees = uber_api.get_eligible_attendees()

#for attendee in attendees:
#    request = requests.post(
#        f'{TUBER_URL}/api/uber_login', json={"token": attendee})
#    print(f"{request.status_code}: {request.text.strip()}")

request = requests.post(
    f"{TUBER_URL}/api/uber_department_sync", headers=headers)
print(f"{request.status_code}: {request.text.strip()}")
