from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from . import paths


@dataclass
class AppSettings:
    openrouter_api_key: str = ""
    default_model: str = "anthropic/claude-sonnet-4.6"
    request_timeout_sec: int = 220
    retries: int = 1
    data_root: str = ""
    default_word_min: int = 750
    default_word_max: int = 900

    @classmethod
    def load(cls, path: Path | None = None) -> "AppSettings":
        p = path or paths.settings_path()
        if not p.exists():
            return cls()
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return cls()

        base = cls()
        for k in asdict(base).keys():
            if k in payload:
                setattr(base, k, payload[k])
        return base

    def save(self, path: Path | None = None) -> Path:
        p = path or paths.settings_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")
        return p

    def redacted(self) -> dict:
        d = asdict(self)
        key = d.get("openrouter_api_key", "")
        if key:
            d["openrouter_api_key"] = key[:6] + "..." + key[-4:] if len(key) > 12 else "***"
        return d

    def validate_word_range(self) -> None:
        if self.default_word_min < 200 or self.default_word_max > 3000 or self.default_word_min >= self.default_word_max:
            raise ValueError("Invalid default word range")
