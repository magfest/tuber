def test_force_https(prod_client):
    """http requests made in production mode should receive a redirect to https"""
    resp = prod_client.get("/api/check_initial_setup")
    assert resp.status_code == 302
    assert "Location" in resp.headers
    assert resp.headers['Location'].startswith("https")

def test_nodouble_redirect(prod_client):
    """https requests made in production mode should not receive a second redirect"""
    resp = prod_client.get("/api/check_initial_setup", base_url="https://localhost")
    assert resp.status_code == 200