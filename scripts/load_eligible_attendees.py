from secrets import TUBER_URL
import uber_api
import requests

attendees = uber_api.get_eligible_attendees()

for attendee in attendees:
    request = requests.post(f'{TUBER_URL}/api/uber_login', json={ "token": attendee })
    print(f"{request.status_code}: {request.text.strip()}")
