from __future__ import annotations

import json
import urllib.error
import urllib.request


class OpenRouterClient:
    def __init__(self, api_key: str, timeout_sec: int = 220, referer: str = "https://uoffer-portable.local"):
        self.api_key = api_key.strip()
        self.timeout_sec = int(timeout_sec)
        self.referer = referer

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def chat(self, model: str, prompt: str, x_title: str = "Uoffer Portable App") -> tuple[str, dict]:
        if not self.api_key:
            raise RuntimeError("OpenRouter API key is not configured.")
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.referer,
                "X-Title": x_title,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"OpenRouter HTTP {e.code}: {e.read().decode(errors='ignore')}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"OpenRouter network error: {e}") from e

        try:
            content = data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            raise RuntimeError(f"Malformed OpenRouter response: {data}") from exc
        usage = data.get("usage", {})
        return content, usage
