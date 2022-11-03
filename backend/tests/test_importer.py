import io

def test_csv_export(client):
    """Try exporting a table and make sure it matches the expected contents."""
    badge = client.post("/api/event/1/badge", json={
        "legal_name": "Test User",
        "departments": []
    }).json
    assert(badge['legal_name'] == "Test User")

    export = client.get("/api/importer/csv", query_string={"csv_type": "Badge"}).data.decode('UTF-8').strip()
    assert(len(export.split("\n")) == 2)
    header, exported_badge = export.split("\n")
    header = header.split(",")
    exported_badge = exported_badge.split(",")
    badge_dict = {k:v for k,v in zip(header, exported_badge)}
    assert(badge_dict['legal_name'] == "Test User")

def test_csv_import(client):
    new_badge = client.post("/api/importer/csv", content_type="multipart/form-data", data={
        "csv_type": "Badge",
        "raw_import": "false",
        "full_import": "false",
        "files": (io.BytesIO(b"legal_name,event\nTest User 1,1"), 'badge.csv')
    })
    assert new_badge.status_code == 200

    badges = client.get("/api/event/1/badge").json
    assert(len(badges) == 1)

    client.post("/api/importer/csv", content_type="multipart/form-data", data={
        "csv_type": "Badge",
        "raw_import": False,
        "full_import": False,
        "files": (io.BytesIO(b"legal_name,event\nTest User 2,1"), 'badge.csv')
    })
    badges = client.get("/api/event/1/badge").json
    assert(len(badges) == 2)

    client.post("/api/importer/csv", content_type="multipart/form-data", data={
        "csv_type": "Badge",
        "raw_import": False,
        "full_import": True,
        "files": (io.BytesIO(b"legal_name,event\nTest User 3,1"), 'badge.csv')
    })
    badges = client.get("/api/event/1/badge", query_string={"full": True}).json
    assert(len(badges) == 1)
    assert(badges[0]['legal_name'] == "Test User 3")