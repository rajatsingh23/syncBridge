import requests


class HTTPClient:
    def __init__(self, connect_timeout=3, read_timeout=10):
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout

    def get(self, url, **kwargs):
        return requests.get(
            url,
            timeout=(self.connect_timeout, self.read_timeout),
            **kwargs,
        )

    def post(self, url, **kwargs):
        return requests.post(
            url,
            timeout=(self.connect_timeout, self.read_timeout),
            **kwargs,
        )

    def patch(self, url, **kwargs):
        return requests.patch(
            url,
            timeout=(self.connect_timeout, self.read_timeout),
            **kwargs,
        )

    def put(self, url, **kwargs):
        return requests.put(
            url,
            timeout=(self.connect_timeout, self.read_timeout),
            **kwargs,
        )

    def delete(self, url, **kwargs):
        return requests.delete(
            url,
            timeout=(self.connect_timeout, self.read_timeout),
            **kwargs,
        )