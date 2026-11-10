import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from mathtutor_pi.site_client import PrintableWorksheet, SiteClient, SiteError

TOKEN = "mt_secret123"


class Stub:
    def __init__(self, status=200, body=b"{}", delay=0.0):
        self.status, self.body, self.delay = status, body, delay
        self.requests = []
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def _handle(self):
                length = int(self.headers.get("Content-Length") or 0)
                if length:
                    self.rfile.read(length)
                stub.requests.append(
                    (self.command, self.path, self.headers.get("Authorization"))
                )
                time.sleep(stub.delay)
                try:
                    self.send_response(stub.status)
                    self.send_header("Content-Length", str(len(stub.body)))
                    self.end_headers()
                    self.wfile.write(stub.body)
                except OSError:
                    pass

            do_GET = do_POST = _handle

            def log_message(self, *args):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


@pytest.fixture
def stub():
    made = []

    def make(**kw):
        s = Stub(**kw)
        made.append(s)
        return s

    yield make
    for s in made:
        s.close()


def client(stub, timeout=2.0):
    return SiteClient(stub.url, TOKEN, timeout)


def test_new_worksheet_posts_bearer_and_parses(stub):
    body = json.dumps({"worksheet_id": "w", "serial": "WS-abc", "html": "<html>"})
    s = stub(status=201, body=body.encode())
    ws = client(s).new_worksheet("c1")
    assert ws == PrintableWorksheet("WS-abc", "<html>")
    assert s.requests == [("POST", "/api/children/c1/worksheets", f"Bearer {TOKEN}")]


def test_child_id_is_url_quoted(stub):
    s = stub(status=404, body=b"{}")
    with pytest.raises(SiteError):
        client(s).new_worksheet("a/b c")
    assert s.requests[0][1] == "/api/children/a%2Fb%20c/worksheets"


def test_trailing_slash_in_base_url(stub):
    s = stub(status=200, body=b'{"children": []}')
    SiteClient(s.url + "/", TOKEN, 2).children()
    assert s.requests[0][1] == "/api/children"


def test_children_returns_list(stub):
    kids = [{"id": "c1", "name": "Philip", "age": 7, "grade": 2}]
    s = stub(body=json.dumps({"children": kids}).encode())
    assert client(s).children() == kids
    assert s.requests == [("GET", "/api/children", f"Bearer {TOKEN}")]


def test_unauthorized_raises_without_token_in_message(stub):
    c = client(stub(status=401))
    with pytest.raises(SiteError) as e:
        c.new_worksheet("c1")
    assert "unauthorized" in str(e.value)
    assert TOKEN not in str(e.value) and TOKEN not in repr(c)


def test_404_raises_child_not_found(stub):
    with pytest.raises(SiteError, match="child not found"):
        client(stub(status=404, body=b'{"error": "not found"}')).new_worksheet("x")


def test_server_error_reports_status(stub):
    with pytest.raises(SiteError, match="http 500"):
        client(stub(status=500)).new_worksheet("c1")


def test_timeout_raises_site_error(stub):
    with pytest.raises(SiteError, match="timeout"):
        client(stub(delay=0.5), timeout=0.2).new_worksheet("c1")


def test_connection_refused_raises_site_error(stub):
    s = stub()
    url = s.url
    s.close()
    with pytest.raises(SiteError) as e:
        SiteClient(url, TOKEN, 1).new_worksheet("c1")
    assert TOKEN not in str(e.value)


def test_bad_json_raises_site_error(stub):
    with pytest.raises(SiteError, match="bad response"):
        client(stub(status=201, body=b"not json")).new_worksheet("c1")


def test_missing_fields_raise_site_error(stub):
    with pytest.raises(SiteError, match="bad response"):
        client(stub(status=201, body=b'{"serial": "x"}')).new_worksheet("c1")


def test_children_bad_shape_raises(stub):
    with pytest.raises(SiteError, match="bad response"):
        client(stub(body=b'{"nope": 1}')).children()
