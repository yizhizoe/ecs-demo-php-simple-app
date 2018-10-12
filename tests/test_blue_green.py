import requests
import os

def test_green_service(port='8080'):
    alb_url = os.getenv('ALB_URL')
    response = requests.get(':'.join([alb_url, port]))
    assert response.status_code == 200
    assert 'V4' in response.text