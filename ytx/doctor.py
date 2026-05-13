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
    required: bool = True
    hint: str = ""


def _which(name: str, *, required: bool = True, hint: str = "") -> Check:
    p = shutil.which(name)
    return Check(name, ok=bool(p), detail=p or "not in PATH", required=required, hint=hint)


def _yt_dlp_version() -> Check:
    if not shutil.which("yt-dlp"):
        return Check("yt-dlp version", False, "not installed", True, "Install/upgrade: brew install yt-dlp or pipx install yt-dlp")
    try:
        v = subprocess.check_output(["yt-dlp", "--version"], text=True).strip()
        return Check("yt-dlp version", True, v)
    except Exception as e:
        return Check("yt-dlp version", False, str(e), True, "Run: yt-dlp -U")


def _python_pkg(name: str, *, required: bool = True, hint: str = "") -> Check:
    try:
        mod = __import__(name)
        v = getattr(mod, "__version__", "installed")
        return Check(f"python:{name}", True, str(v), required=required, hint=hint)
    except ImportError:
        return Check(f"python:{name}", False, "not installed", required=required, hint=hint)


def _disk_free() -> Check:
    import shutil as sh
    total, used, free = sh.disk_usage(REPO_ROOT)
    gb = free / (1024**3)
    return Check("disk free", gb > 5, f"{gb:.1f} GB free", True, "Free at least 5GB before large downloads")


def run() -> list[Check]:
    checks = [
        _which("yt-dlp", hint="Install: brew install yt-dlp or pipx install yt-dlp"),
        _yt_dlp_version(),
        _which("ffmpeg", required=False, hint="Optional for Whisper: brew install ffmpeg"),
        _which("python3"),
        _python_pkg("faster_whisper", required=False, hint="Optional Whisper fallback: pip install faster-whisper"),
        _python_pkg("yaml", required=False, hint="Optional nicer YAML support: pip install pyyaml"),
        _disk_free(),
    ]
    return checks


def render(checks: list[Check]) -> str:
    lines = ["# ytx doctor", ""]
    for c in checks:
        mark = "✓" if c.ok else ("✗" if c.required else "!")
        req = "required" if c.required else "optional"
        lines.append(f"- {mark} {c.name} ({req}): {c.detail}")
        if not c.ok and c.hint:
            lines.append(f"  - fix: {c.hint}")
    missing_required = [c for c in checks if c.required and not c.ok]
    missing_optional = [c for c in checks if not c.required and not c.ok]
    lines.append("")
    if missing_required:
        lines.append(f"Required issues: {len(missing_required)}")
    else:
        lines.append("Required environment: PASS")
    if missing_optional:
        lines.append(f"Optional enhancements missing: {len(missing_optional)}")
    return "\n".join(lines)


def required_ok(checks: list[Check]) -> bool:
    return all(c.ok for c in checks if c.required)
