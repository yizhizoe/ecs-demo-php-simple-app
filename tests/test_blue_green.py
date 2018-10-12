import requests
import os

def test_green_service(port='8080'):
    alb_url = os.getenv('ALB_URL')
    print (alb_url)
    response = requests.get(':'.join([alb_url, port]))
    assert 'V4' in response