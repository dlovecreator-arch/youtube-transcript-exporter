"""Run reports for repeatable maintenance and handoff notes."""
from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from . import audit as audit_mod, doctor as doctor_mod, status as status_mod
from .config import REPO_ROOT


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _git_dirty() -> str:
    try:
        out = subprocess.check_output(["git", "status", "--short"], cwd=REPO_ROOT, text=True).strip()
        return "yes" if out else "no"
    except Exception:
        return "unknown"


def write_report(output_path: Path | None = None) -> Path:
    """Write a markdown operational report and return its path."""
    if output_path is None:
        output_path = REPO_ROOT / "logs" / "runs" / f"ytx_report_{_utc_stamp()}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    status_text = status_mod.render(status_mod.collect())
    audit_text = audit_mod.run(full=False, log_result=False).render()
    doctor_checks = doctor_mod.run()
    doctor_text = doctor_mod.render(doctor_checks)

    content = "\n\n".join(
        [
            "# ytx Run Report",
            f"- Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"- Git commit: `{_git_commit()}`",
            f"- Git dirty: `{_git_dirty()}`",
            "- Scope: status, quick audit, required/optional dependency check",
            status_text,
            audit_text,
            doctor_text,
            "## Recommended safe next steps",
            "1. Review any warnings above.",
            "2. Run `python3 -m ytx fix` for a dry-run self-healing plan.",
            "3. Run `python3 -m ytx update` only when you are ready to download new channel content.",
            "4. Run `python3 -m ytx export chunks --out exports/chunks.jsonl` when you want a fresh RAG export.",
        ]
    )
    output_path.write_text(content + "\n", encoding="utf-8")
    return output_path
