import time

def test_fast_request(client):
    """Make sure that fast requests do not create a job."""
    result = client.get("/api/fast")
    assert result.status_code == 200

def test_slow_request(client):
    """Make sure that slow requests do create a job."""
    result = client.get("/api/slow")
    assert result.status_code == 202

def test_job_retrieval(client):
    """Make sure jobs can be retrieved after a long running job is started."""
    result = client.get("/api/slow")
    assert result.status_code == 202
    assert "Location" in result.headers
    url = result.headers['Location']
    start_time = time.time()
    while time.time() - start_time < 15:
        result = client.get(url)
        time.sleep(0.2)
        if result.status_code == 202:
            assert "complete" in result.json
            assert not result.json['complete']
        if result.status_code == 200:
            break
    assert result.json
    assert "amount" in result.json
    assert "complete" in result.json
    assert "messages" in result.json
    assert "status" in result.json