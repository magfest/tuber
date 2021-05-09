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
    assert "job" in result.json
    job_id = result.json['job']
    start_time = time.time()
    while time.time() - start_time < 15:
        result = client.get("/api/jobs", query_string={"job": job_id})
        assert result.status_code == 200
        assert "progress" in result.json
        assert "complete" in result.json['progress']
        assert "result" in result.json
        if result.json['progress']['complete']:
            break
    print(result.json)
    assert result.json['result']['status_code'] == 200
    assert result.json['result']['data'] == "success"
    assert result.json['result']['mimetype'] == "text/html"
    assert result.json['result']['headers']
    assert result.json['result']['execution_time']
