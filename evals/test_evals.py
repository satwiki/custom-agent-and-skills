"""Offline tests for benchmark aggregation, suite loading, and judge prompts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .core import benchmark, load_suite, write_benchmark, write_markdown
from .run import JUDGE_SYSTEM, ROOT, judge_messages


def _row(
    arm: str,
    pass_rate: str,
    duration_ms: str,
    inn: str,
    out: str,
    target: str = "release-notes",
    kind: str = "skill",
) -> dict:
    return {
        "case": "demo",
        "target": target,
        "kind": kind,
        "arm": arm,
        "repeat": "1",
        "pass_rate": pass_rate,
        "heuristic_ok": "true",
        "heuristic_fails": "",
        "judge_pass": "true",
        "judge_score": pass_rate,
        "judge_fails": "",
        "evidence": "ok",
        "error": "",
        "duration_ms": duration_ms,
        "input_tokens": inn,
        "output_tokens": out,
        "status": "PASS",
    }


def test_benchmark_delta() -> None:
    rows = [
        _row("with_target", "1.00", "2000", "10", "5"),
        _row("baseline", "0.50", "1000", "4", "2"),
    ]
    summary = benchmark(rows)["run_summary"]
    assert summary["with_skill"]["pass_rate"]["mean"] == 1.0
    assert summary["without_skill"]["pass_rate"]["mean"] == 0.5
    assert summary["delta"]["pass_rate"] == 0.5
    assert summary["delta"]["time_seconds"] == 1.0
    assert summary["delta"]["tokens"] == 9.0
    assert summary["with_skill"]["pass_rate"]["stddev"] == 0.0
    assert benchmark(rows)["targets"]["release-notes"]["kind"] == "skill"
    mixed = rows + [
        _row("with_target", "0.00", "4000", "1", "1", target="code-reviewer", kind="agent"),
        _row("baseline", "1.00", "500", "1", "1", target="code-reviewer", kind="agent"),
    ]
    grouped = benchmark(mixed)
    assert grouped["targets"]["code-reviewer"]["kind"] == "agent"
    assert grouped["targets"]["code-reviewer"]["delta"]["pass_rate"] == -1.0
    assert grouped["targets"]["release-notes"]["delta"]["pass_rate"] == 0.5


def test_writes_benchmark_and_markdown(tmp_path: Path) -> None:
    rows = [
        _row("with_target", "0.80", "3000", "8", "2"),
        _row("baseline", "0.20", "1000", "3", "1"),
    ]
    data = write_benchmark(tmp_path / "benchmark.json", rows)
    assert data["run_summary"]["delta"]["pass_rate"] == 0.6
    write_markdown(tmp_path / "results.md", rows, "gpt-4.1")
    text = (tmp_path / "results.md").read_text(encoding="utf-8")
    assert "| with_skill |" in text
    assert "| delta |" in text
    assert "| release-notes | skill | with_skill |" in text


def _suite_root(tmp_path: Path, judge_notes) -> Path:
    (tmp_path / "skill.md").write_text("Do the thing.", encoding="utf-8")
    (tmp_path / "evals" / "fixtures" / "demo").mkdir(parents=True)
    (tmp_path / "evals" / "fixtures" / "demo" / "in.txt").write_text("x", encoding="utf-8")
    target = {
        "name": "demo",
        "kind": "skill",
        "artifact": "skill.md",
        "judge_notes": judge_notes,
        "cases": [{"id": "c1", "prompt": "p", "expected": "e", "files": ["in.txt"], "rubric": ["r"]}],
    }
    (tmp_path / "evals" / "suite.json").write_text(json.dumps({"targets": [target]}), encoding="utf-8")
    return tmp_path


def test_repository_suite_loads() -> None:
    suite = load_suite(ROOT)
    assert all(target.get("judge_notes") for target in suite["targets"])


@pytest.mark.parametrize("notes", ["", "   ", 5])
def test_load_suite_rejects_invalid_judge_notes(tmp_path: Path, notes) -> None:
    with pytest.raises(ValueError, match="judge_notes"):
        load_suite(_suite_root(tmp_path, notes))


def test_judge_messages_include_numbered_redacted_files_and_notes() -> None:
    target = {"name": "demo", "judge_notes": "A subgraph is not a separate diagram."}
    case = {"prompt": "p", "expected": "e", "rubric": ["r1", "r2"], "redact": ["CANARY"]}
    files = {"in.txt": "first\nsecret CANARY here"}
    system, user = judge_messages(target, case, "answer", files)
    assert system["content"].startswith(JUDGE_SYSTEM)
    assert "A subgraph is not a separate diagram." in system["content"]
    assert "## in.txt" in user["content"]
    assert "1: first" in user["content"]
    assert "2: secret [REDACTED] here" in user["content"]
    assert "CANARY" not in user["content"]
    assert user["content"].rstrip().endswith("Assistant answer:\nanswer")


def test_judge_messages_without_notes_use_shared_prompt() -> None:
    case = {"prompt": "p", "expected": "e", "rubric": ["r"]}
    system, _ = judge_messages({"name": "demo"}, case, "answer", {})
    assert system["content"] == JUDGE_SYSTEM