import json
import requests

with open("dump.json", "r") as dump:
    rooms = json.load(dump)['rooms']

for room in rooms:
    headers = {
        "Cookie": "",
        "CSRF-Token": ""
    }
    req = requests.post("https://super2023.reggie.magfest.org/hotel_admin/delete_room?id="+room['id'], headers=headers)
    print(req.status_code)