"""GitHub REST client: stdlib only, with call accounting, rate-limit awareness and a budget."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request


class GitHubError(RuntimeError):
    pass


class BudgetExhausted(GitHubError):
    pass


class Client:
    def __init__(self, token: str, api_url: str = "https://api.github.com", reserve: int = 25,
                 max_calls: int = 400, opener=None):
        if not token:
            raise GitHubError("github-token is required (pass secrets.GITHUB_TOKEN to the action)")
        self.token, self.api_url = token, api_url.rstrip("/")
        self.reserve, self.max_calls = reserve, max_calls
        self.calls, self.remaining = 0, None
        self._open = opener or urllib.request.urlopen

    def affordable(self, n: int = 1) -> bool:
        """Can we spend n more calls without eating into the reserve?"""
        if self.calls + n > self.max_calls:
            return False
        return self.remaining is None or self.remaining - n > self.reserve

    def get(self, path: str, params: dict | None = None, *, essential: bool = False):
        if not essential and not self.affordable():
            raise BudgetExhausted(path)
        url = f"{self.api_url}{path}" + ("?" + urllib.parse.urlencode(params) if params else "")
        request = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "observstory-action",
        })
        for attempt in range(3):
            self.calls += 1
            try:
                with self._open(request, timeout=30) as response:
                    self._note(response.headers)
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                self._note(exc.headers or {})
                body = exc.read().decode("utf-8", errors="replace")[:300]
                retry_after = (exc.headers or {}).get("Retry-After")
                if exc.code in (403, 429) and (retry_after or self.remaining == 0):
                    wait = min(int(retry_after or 30), 60)
                    if attempt < 2 and wait <= 60:
                        time.sleep(wait)
                        continue
                    raise BudgetExhausted(f"rate limited on {path}") from exc
                if exc.code >= 500 and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                hint = {401: " (token invalid)", 403: " (missing permission? the workflow needs contents/pull-requests/issues: read)",
                        404: " (repository not found or token lacks access)"}.get(exc.code, "")
                raise GitHubError(f"GitHub API {exc.code} for {path}{hint}: {body}") from exc
            except urllib.error.URLError as exc:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise GitHubError(f"network error for {path}: {exc.reason}") from exc
        raise GitHubError(f"giving up on {path}")

    def _note(self, headers):
        value = headers.get("X-RateLimit-Remaining") if hasattr(headers, "get") else None
        if value is not None:
            try:
                self.remaining = int(value)
            except ValueError:
                pass
