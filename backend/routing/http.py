import time
import requests


RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def request(method, url, retries=2, **kwargs):
    for attempt in range(retries + 1):
        try:
            response = requests.request(method, url, **kwargs)
            if response.status_code not in RETRYABLE_STATUS or attempt == retries:
                return response
        except (requests.ConnectionError, requests.Timeout):
            if attempt == retries:
                raise
        time.sleep(0.5 * 2 ** attempt)
