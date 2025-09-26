def test_metrics_endpoint(client):
    """Test the metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.data.decode("utf-8")

    assert data.startswith("# HELP")
    # Should have both process and python data
    assert "process_" in data and "python_" in data
