"""Smoke-check a running static dashboard container without a browser."""

from html.parser import HTMLParser
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self.styles = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script' and attrs.get('src'):
            self.scripts.append(attrs['src'])
        if tag == 'link' and attrs.get('rel') == 'stylesheet' and attrs.get('href'):
            self.styles.append(attrs['href'])


def check(base):
    def fetch(path):
        parsed = urlsplit(path)
        if parsed.scheme or parsed.netloc or not path.startswith('/'):
            raise AssertionError('Expected a same-origin absolute path')
        try:
            with urlopen(base.rstrip('/') + path, timeout=5) as response:
                return response.status, response.headers.get_content_type(), response.read()
        except HTTPError as exc:
            with exc:
                return exc.code, exc.headers.get_content_type(), exc.read()

    health = None
    for _ in range(20):
        try:
            health = fetch('/health')
            if health[0] == 200:
                break
        except URLError:
            pass
        time.sleep(0.5)
    assert health and health[0] == 200 and health[2].strip() == b'healthy', 'Health endpoint failed'
    print('PASS health endpoint')

    status, mime, html = fetch('/')
    assert status == 200 and mime == 'text/html' and b'id="root"' in html, 'Dashboard HTML missing'
    print('PASS dashboard HTML')
    status, mime, deep = fetch('/analytics')
    assert status == 200 and mime == 'text/html' and deep == html, 'SPA deep-link fallback failed'
    print('PASS SPA deep link')

    assets = Assets()
    assets.feed(html.decode('utf-8'))
    assert assets.scripts and assets.styles, 'Built JavaScript or CSS references missing'
    for path in assets.scripts:
        status, mime, body = fetch(path)
        assert status == 200 and mime in ('text/javascript', 'application/javascript'), 'JavaScript response invalid'
        assert len(body) > 1000 and b'<html' not in body[:100].lower(), 'JavaScript asset missing'
    print('PASS built JavaScript assets')
    styles = []
    for path in assets.styles:
        status, mime, body = fetch(path)
        assert status == 200 and mime == 'text/css', 'CSS response invalid'
        styles.append(body)
    css = b'\n'.join(styles)
    assert b'@tailwind' not in css and b'.grid-cols-4' in css, 'Tailwind utilities were not compiled'
    print('PASS compiled CSS assets')

    status, mime, body = fetch('/api/health')
    assert status == 503 and mime == 'application/json', 'Unconfigured API must report HTTP 503'
    assert json.loads(body)['error'] == 'Dashboard API integration is not configured', 'API boundary message missing'
    print('PASS explicit API boundary')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: python3 scripts/check-dashboard-http.py http://127.0.0.1:3002')
    check(sys.argv[1])
