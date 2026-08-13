import base64
import os
import re
import time

import requests
from dotenv import load_dotenv

load_dotenv()

API_ROOT = "https://api.github.com"


class GitHubClient:
    def __init__(self, token=None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise RuntimeError("GITHUB_TOKEN not set (check .env)")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def _request(self, method, path, **kwargs):
        url = path if path.startswith("http") else f"{API_ROOT}{path}"
        while True:
            resp = self.session.request(method, url, **kwargs)
            if resp.status_code == 403 and "rate limit" in resp.text.lower():
                reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 30))
                wait = max(reset - time.time(), 1)
                time.sleep(min(wait, 60))
                continue
            if resp.status_code == 403 and resp.headers.get("Retry-After"):
                time.sleep(int(resp.headers["Retry-After"]))
                continue
            return resp

    def get(self, path, params=None):
        return self._request("GET", path, params=params)

    def get_json(self, path, params=None):
        resp = self.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    def paginate(self, path, params=None, per_page=100):
        params = dict(params or {})
        params["per_page"] = per_page
        page = 1
        while True:
            params["page"] = page
            resp = self.get(path, params=params)
            resp.raise_for_status()
            items = resp.json()
            if not items:
                break
            yield from items
            if len(items) < per_page:
                break
            page += 1

    def count_via_last_page(self, path, params=None, cap_pages=5):
        """Cheap count using the Link header's last page number (per_page=1).
        Caps at cap_pages*1 items to avoid burning rate limit on huge histories;
        returns (count, capped)."""
        params = dict(params or {})
        params["per_page"] = 1
        params["page"] = 1
        resp = self.get(path, params=params)
        resp.raise_for_status()
        link = resp.headers.get("Link", "")
        match = re.search(r'page=(\d+)>; rel="last"', link)
        if match:
            total = int(match.group(1))
            if total > cap_pages * 1:
                return cap_pages * 1, True
            return total, False
        data = resp.json()
        return (1 if data else 0), False

    def get_readme_text(self, owner, name, max_chars=6000):
        resp = self.get(f"/repos/{owner}/{name}/readme")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return content[:max_chars]

    def search_count(self, query):
        """Uses the Search API's total_count. Search has a strict ~30/min
        secondary rate limit, so callers should throttle between calls."""
        data = self.get_json("/search/issues", params={"q": query, "per_page": 1})
        return data.get("total_count", 0)
