import requests


class HTTPClient:
    def __init__(self, timeout=10):
        self.timeout = timeout

    def get(self, url, **kwargs):
        return requests.get(
            url,
            timeout=self.timeout,
            **kwargs,
        )

    def post(self, url, **kwargs):
        return requests.post(
            url,
            timeout=self.timeout,
            **kwargs,
        )

    def patch(self, url, **kwargs):
        return requests.patch(
            url,
            timeout=self.timeout,
            **kwargs,
        )

    def put(self, url, **kwargs):
        return requests.put(
            url,
            timeout=self.timeout,
            **kwargs,
        )

    def delete(self, url, **kwargs):
        return requests.delete(
            url,
            timeout=self.timeout,
            **kwargs,
        )