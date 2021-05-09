import time

def test_fast_request_redis(client):
    """Make sure that fast requests do not create a job when using redis."""
    result = client.get("/api/fast")
    assert result.status_code == 200

def test_slow_request_redis(client):
    """Make sure that slow requests do create a job when using redis."""
    result = client.get("/api/slow")
    assert result.status_code == 202

def test_fast_request_no_redis(client_noredis):
    """Make sure that fast requests do not create a job when not using redis."""
    result = client_noredis.get("/api/fast")
    assert result.status_code == 200

def test_slow_request_no_redis(client_noredis):
    """Make sure that slow requests do create a job when not using redis."""
    result = client_noredis.get("/api/slow")
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
        if result.json['result']:
            assert result.json['progress']['complete']
            break
        else:
            assert not result.json['progress']['complete']
    assert result.json['result']['status_code'] == 200
    assert result.json['result']['data'] == "success"
    assert result.json['result']['mimetype'] == "text/html"
    assert result.json['result']['headers']
    assert result.json['result']['execution_time']

def test_job_retrieval_noredis(client_noredis):
    """Make sure jobs can be retrieved after a long running job is started."""
    client = client_noredis
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
        if result.json['result']:
            assert result.json['progress']['complete']
            break
        else:
            assert not result.json['progress']['complete']
    print(result.json)
    assert result.json['result']['status_code'] == 200
    assert result.json['result']['data'] == "success"
    assert result.json['result']['mimetype'] == "text/html"
    assert result.json['result']['headers']
    assert result.json['result']['execution_time']
