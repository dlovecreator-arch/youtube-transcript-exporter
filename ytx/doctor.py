"""Doctor -- diagnose the environment before you blame the code."""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from .config import REPO_ROOT


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


def _which(name: str) -> Check:
    p = shutil.which(name)
    return Check(name, ok=bool(p), detail=p or "not in PATH")


def _yt_dlp_version() -> Check:
    if not shutil.which("yt-dlp"):
        return Check("yt-dlp version", False, "not installed")
    try:
        v = subprocess.check_output(["yt-dlp", "--version"], text=True).strip()
        return Check("yt-dlp version", True, v)
    except Exception as e:
        return Check("yt-dlp version", False, str(e))


def _python_pkg(name: str) -> Check:
    try:
        mod = __import__(name)
        v = getattr(mod, "__version__", "installed")
        return Check(f"python:{name}", True, str(v))
    except ImportError:
        return Check(f"python:{name}", False, "not installed")


def _disk_free() -> Check:
    import shutil as sh
    total, used, free = sh.disk_usage(REPO_ROOT)
    gb = free / (1024**3)
    return Check("disk free", gb > 5, f"{gb:.1f} GB free")


def run() -> list[Check]:
    checks = [
        _which("yt-dlp"),
        _yt_dlp_version(),
        _which("ffmpeg"),
        _which("python3"),
        _python_pkg("faster_whisper"),
        _python_pkg("yaml"),
        _disk_free(),
    ]
    return checks


def render(checks: list[Check]) -> str:
    lines = ["# ytx doctor", ""]
    for c in checks:
        mark = "✓" if c.ok else "✗"
        lines.append(f"- {mark} {c.name}: {c.detail}")
    return "\n".join(lines)
