from tests.test_room_matching import _seed


def test_match_stats(client):
    """Five people on two nights: four want both, one only Friday."""
    import tuber.config
    import tuber.models as models
    from tuber.database import db
    tuber.config.gender_map = {"woman": "F", "man": "M"}

    names = ["Alice One", "Bob Two", "Carol Three", "Dave Four", "Erin Five"]
    s = _seed(db, models, names,
              roommate_pairs=[("Alice One", "Bob Two"), ("Bob Two", "Alice One"),
                              ("Carol Three", "Erin Five")],
              anti_pairs=[("Erin Five", "Carol Three")])
    friday, saturday = [x.id for x in s["nights"]]
    db.query(models.RoomNightRequest).filter(
        models.RoomNightRequest.badge == s["badges"]["Erin Five"].id,
        models.RoomNightRequest.room_night == saturday).delete()
    s["requests"]["Alice One"].prefer_single_gender = True
    s["requests"]["Alice One"].preferred_gender = "Woman"
    s["requests"]["Carol Three"].preferred_gender = "woman"
    s["requests"]["Bob Two"].preferred_gender = "man"
    s["requests"]["Dave Four"].preferred_gender = "wizard"
    db.commit()

    rv = client.get("/api/event/1/hotel/match_stats")
    assert rv.status_code == 200
    block = rv.json[0]
    assert block["open_requests"] == 5
    assert block["no_nights_requested"] == 0 and block["no_eligible_nights"] == 0

    nights = block["nights"]
    assert [x["people"] for x in nights["per_night"]] == [5, 4]
    assert nights["room_night_floor"] == 3          # Fri: 2 rooms, Sat: 1 room
    assert nights["min_rooms"] == 2                 # Friday's 5 people
    assert nights["peak_night"] == {"name": "Friday", "people": 5}
    assert nights["exact_pattern_rooms"] == 2       # 4 on Fri+Sat, 1 on Fri alone
    assert nights["exact_pattern_room_nights"] == 3  # 4x Fri+Sat -> 2, 1x Fri -> 1
    assert nights["distinct_patterns"] == 2 and nights["unique_patterns"] == 1
    assert nights["pattern_leftovers"] == 1

    mates = block["roommates"]
    assert mates["mutual_pairs"] == 1 and mates["one_way"] == 1
    assert mates["pairs_identical_nights"] == 1
    assert mates["groups"] == [{"size": 2, "groups": 1, "matching_nights": 1}]
    assert mates["anti_requests"] == 1 and mates["conflicts"] == 1

    gender = block["gender"]
    assert gender["requesters"] == 1
    assert gender["buckets"] == [{"gender": "F", "mapped": True, "requesters": 1, "people": 2}]
    assert gender["blank"] == 1
    assert gender["unmapped_answers"] == ["wizard"]


def test_match_stats_groups_by_size(client):
    """A trio where one member is approved for fewer nights doesn't match;
       a pair on identical nights does."""
    import tuber.models as models
    from tuber.database import db

    names = ["Alice One", "Bob Two", "Carol Three", "Dave Four", "Erin Five"]
    trio, pair = names[:3], names[3:]
    mutual = [(a, b) for group in (trio, pair) for a in group for b in group if a != b]
    s = _seed(db, models, names, roommate_pairs=mutual)
    friday, saturday = s["nights"]
    saturday.restriction_mode = "manual"
    for name in ["Alice One", "Bob Two", "Dave Four", "Erin Five"]:
        db.add(models.RoomNightApproval(event=1, badge=s["badges"][name].id,
                                        room_night=saturday.id, approved=True))
    db.commit()

    groups = client.get("/api/event/1/hotel/match_stats").json[0]["roommates"]["groups"]
    assert groups == [{"size": 2, "groups": 1, "matching_nights": 1},
                      {"size": 3, "groups": 1, "matching_nights": 0}]
    # On requested nights, Carol's unapproved Saturday counts and the trio lines up.
    groups = client.get("/api/event/1/hotel/match_stats",
                        query_string={"nights": "requested"}).json[0]["roommates"]["groups"]
    assert groups[1] == {"size": 3, "groups": 1, "matching_nights": 1}
