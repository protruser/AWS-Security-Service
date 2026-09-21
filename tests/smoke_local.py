"""Run against Compose: python tests/smoke_local.py.

Creates one fictional review and one order, retained in the local database.
"""
import http.cookiejar
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = os.getenv("SMOKE_BASE_URL", "http://localhost:5000")
LAB = os.getenv("SMOKE_VULNERABLE_LAB", "1") == "1"
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def request(path, data=None, expected=200):
    payload = urllib.parse.urlencode(data).encode() if data is not None else None
    try:
        response = client.open(BASE + path, data=payload, timeout=10)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = response.read().decode()
        assert response.status == expected, (path, response.status)
        assert response.headers.get("X-Request-ID"), path
        print(f"PASS {path}: HTTP {response.status}, request ID present")
        return body


def csrf(path="/login"):
    return re.search(r'name="csrf_token" value="([^"]+)"', request(path)).group(1)


def main():
    assert json.loads(request("/health"))["status"] == "healthy"
    assert json.loads(request("/ready"))["database"] == "connected"
    assert "데모 키보드" in request("/products")
    assert "데모 키보드" in request("/search?q=" + urllib.parse.quote("키보드"))
    request("/missing-smoke", expected=404)
    request("/orders", {"product_id": 1, "quantity": 1}, expected=401)
    request("/products/1/reviews", {"content": "unauthenticated"}, expected=401)
    request("/login", {"csrf_token": csrf(), "username": "demo_user1", "password": "wrong-demo-password"}, expected=401)
    request("/login", {"csrf_token": csrf(), "username": "demo_user1", "password": "DemoUser1!2026"})
    token = csrf("/products/1")
    request("/products/1/reviews", {"csrf_token": token, "content": "로컬 HTTP 검증용 더미 후기 <b>encoded</b>"})
    expected_review = "<b>encoded</b>" if LAB else "&lt;b&gt;encoded&lt;/b&gt;"
    assert expected_review in request("/products/1/reviews")
    request("/orders", {"csrf_token": token, "product_id": 1, "quantity": 1})
    assert "데모 키보드" in request("/orders")
    request("/logout", {"csrf_token": token})
    request("/login", {"csrf_token": csrf(), "username": "demo_admin", "password": "DemoAdmin!2026"})
    assert "관리자" in request("/products")
    assert "데모 키보드" not in request("/orders")
    print("All local MySQL HTTP smoke checks passed.")


if __name__ == "__main__":
    main()
