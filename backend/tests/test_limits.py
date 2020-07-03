def test_limits(client):
    """Make sure that requesting resources with limits return a slice of the result."""
    for i in range(100):
        badge = client.post("/api/events/1/badges", json={
            "legal_name": "Test User {}".format(i)
        }).json
        assert(badge['legal_name'] == "Test User {}".format(i))
    badges = client.get("/api/events/1/badges", query_string={"limit": 10}).json
    assert(len(badges) == 10)
    
def test_offset(client):
    """Make sure that requesting resources with offsets return the correct range of data."""
    for i in range(100):
        badge = client.post("/api/events/1/badges", json={
            "legal_name": "Test User {}".format(i)
        }).json
        assert(badge['legal_name'] == "Test User {}".format(i))
    badges = client.get("/api/events/1/badges", query_string={"offset": 10, "limit": 10, "full": True}).json
    assert(len(badges) == 10)
    assert(badges[0]["legal_name"] == "Test User 10")

def test_page(client):
    """Make sure that requesting resources with pagination return the correct data."""
    for i in range(100):
        badge = client.post("/api/events/1/badges", json={
            "legal_name": "Test User {}".format(i)
        }).json
        assert(badge['legal_name'] == "Test User {}".format(i))
    badges = client.get("/api/events/1/badges", query_string={"page": 3, "limit": 15, "full": True}).json
    assert(len(badges) == 15)
    assert(badges[0]["legal_name"] == "Test User 45")