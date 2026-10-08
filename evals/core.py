"""Load suite.json, run regex heuristics, write a markdown report."""

from __future__ import annotations

import json
import re
from pathlib import Path

FLAGS = re.IGNORECASE | re.MULTILINE


def instruction_body(text: str) -> str:
    """Strip optional YAML frontmatter."""
    return re.sub(r"^---\r?\n[\s\S]*?\r?\n---\r?\n", "", text).strip()


def contained_file(root: Path, relative: str) -> Path:
    """Resolve a file inside root; reject absolute paths and `..`."""
    if not relative or Path(relative).anchor:
        raise ValueError("Expected a relative file path")
    base = root.resolve(strict=True)
    filename = (base / relative).resolve(strict=True)
    if filename == base or not filename.is_relative_to(base) or not filename.is_file():
        raise ValueError(f"File is outside the fixture: {relative}")
    return filename


def redact(text: str, values: list[str]) -> str:
    """Replace secret-like values with [REDACTED]."""
    for value in values:
        if value:
            text = text.replace(value, "[REDACTED]")
    return text


def load_suite(root: Path) -> dict:
    """Load targets, attach instruction text, and check required fields."""
    suite = json.loads((root / "evals" / "suite.json").read_text(encoding="utf-8"))
    ids: set[str] = set()
    for target in suite["targets"]:
        name = target["name"]
        if name in ids:
            raise ValueError(f"Duplicate target: {name}")
        ids.add(name)
        path = contained_file(root, target["artifact"])
        target["instructions"] = instruction_body(path.read_text(encoding="utf-8"))
        if not target["instructions"]:
            raise ValueError(f"Empty instructions: {name}")
        # judge notes provide target-specific instructions
        notes = target.get("judge_notes", None)
        if notes is not None and (not isinstance(notes, str) or not notes.strip()):
            raise ValueError(f"judge_notes must be a non-empty string: {name}")
        for case in target["cases"]:
            case_id = case["id"]
            if case_id in ids:
                raise ValueError(f"Duplicate case: {case_id}")
            ids.add(case_id)
            for file in case["files"]:
                contained_file(root / "evals" / "fixtures" / name, file)
            if not case.get("prompt") or not case.get("expected") or not case.get("rubric"):
                raise ValueError(f"Missing prompt/expected/rubric: {case_id}")
            for heuristic in case.get("heuristics") or []:
                if heuristic["type"] in ("matches", "not_matches"):
                    re.compile(heuristic["pattern"], FLAGS)
                elif heuristic["type"] == "contains_all":
                    for pattern in heuristic["patterns"]:
                        re.compile(pattern, FLAGS)
                else:
                    raise ValueError(f"Unknown heuristic type: {heuristic['type']}")
    return suite


def grade_heuristics(output: str, heuristics: list[dict]) -> list[dict]:
    """Local regex checks. Empty output always fails."""
    results = [{"id": "nonempty", "passed": bool(output.strip()), "evidence": f"{len(output)} characters"}]
    for heuristic in heuristics:
        kind = heuristic["type"]
        if kind in ("matches", "not_matches"):
            match = re.search(heuristic["pattern"], output, FLAGS)
            passed = bool(match) if kind == "matches" else not match
            evidence = f"Matched: {match[0]}" if match else "No match"
        else:
            missing = [p for p in heuristic["patterns"] if not re.search(p, output, FLAGS)]
            passed = not missing
            evidence = "All patterns found" if passed else f"Missing: {', '.join(missing)}"
        results.append({"id": heuristic["id"], "passed": passed, "evidence": evidence})
    return results


def flatten(text: str) -> str:
    """Collapse whitespace and pipes so text fits a markdown cell."""
    compact = re.sub(r"\s+", " ", text).strip().replace("|", "/")
    return compact[:397] + "..." if len(compact) > 400 else compact


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _stddev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    return (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5


def _stat(values: list[float]) -> dict[str, float]:
    return {"mean": round(_mean(values), 2), "stddev": round(_stddev(values), 2)}


def _pair_stats(rows: list[dict]) -> dict:
    """with_skill / without_skill means and the with-minus-without delta."""
    groups = {
        "with_skill": [row for row in rows if row["arm"] == "with_target"],
        "without_skill": [row for row in rows if row["arm"] == "baseline"],
    }
    summary: dict = {}
    for name, group in groups.items():
        rates = [float(row.get("pass_rate") or 0) for row in group]
        times = [int(row["duration_ms"] or 0) / 1000 for row in group]
        tokens: list[float] = []
        for row in group:
            if row.get("input_tokens") or row.get("output_tokens"):
                tokens.append(int(row["input_tokens"] or 0) + int(row["output_tokens"] or 0))
        summary[name] = {
            "pass_rate": _stat(rates),
            "time_seconds": _stat(times),
            "tokens": _stat(tokens),
        }
    with_skill = summary["with_skill"]
    without = summary["without_skill"]
    summary["delta"] = {
        "pass_rate": round(with_skill["pass_rate"]["mean"] - without["pass_rate"]["mean"], 2),
        "time_seconds": round(with_skill["time_seconds"]["mean"] - without["time_seconds"]["mean"], 2),
        "tokens": round(with_skill["tokens"]["mean"] - without["tokens"]["mean"], 2),
    }
    return summary


def benchmark(rows: list[dict]) -> dict:
    """Overall stats plus one with/without group per skill or agent."""
    targets: dict = {}
    seen: list[str] = []
    for row in rows:
        name = row.get("target") or "unknown"
        if name not in seen:
            seen.append(name)
    for name in seen:
        group = [row for row in rows if (row.get("target") or "unknown") == name]
        stats = _pair_stats(group)
        stats["kind"] = group[0].get("kind") or ""
        targets[name] = stats
    return {"run_summary": _pair_stats(rows), "targets": targets}


def write_benchmark(path: Path, rows: list[dict]) -> dict:
    """Write agentskills.io-style benchmark.json."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = benchmark(rows)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def write_markdown(path: Path, rows: list[dict], model: str) -> None:
    """Write a summary table, benchmark, and one section per answer."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = benchmark(rows)
    summary = data["run_summary"]
    lines = [
        "---",
        "title: Evaluation results",
        "description: Heuristic and LLM-judge scores for skill and agent answers",
        "---",
        "",
        "## Summary",
        "",
        f"Model: {model}.",
        "",
        "| Config | Pass rate mean | Pass rate stddev | Time s mean | Tokens mean |",
        "| --- | --- | --- | --- | --- |",
        (
            f"| with_skill | {summary['with_skill']['pass_rate']['mean']:.2f} | "
            f"{summary['with_skill']['pass_rate']['stddev']:.2f} | "
            f"{summary['with_skill']['time_seconds']['mean']:.2f} | "
            f"{summary['with_skill']['tokens']['mean']:.2f} |"
        ),
        (
            f"| without_skill | {summary['without_skill']['pass_rate']['mean']:.2f} | "
            f"{summary['without_skill']['pass_rate']['stddev']:.2f} | "
            f"{summary['without_skill']['time_seconds']['mean']:.2f} | "
            f"{summary['without_skill']['tokens']['mean']:.2f} |"
        ),
        (
            f"| delta | {summary['delta']['pass_rate']:.2f} | n/a | "
            f"{summary['delta']['time_seconds']:.2f} | {summary['delta']['tokens']:.2f} |"
        ),
        "",
        "| Target | Kind | Config | Pass rate mean | Time s mean | Tokens mean |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for name, stats in data["targets"].items():
        kind = stats.get("kind") or "n/a"
        for config in ("with_skill", "without_skill", "delta"):
            block = stats[config]
            if config == "delta":
                lines.append(
                    f"| {name} | {kind} | delta | {block['pass_rate']:.2f} | "
                    f"{block['time_seconds']:.2f} | {block['tokens']:.2f} |"
                )
            else:
                lines.append(
                    f"| {name} | {kind} | {config} | {block['pass_rate']['mean']:.2f} | "
                    f"{block['time_seconds']['mean']:.2f} | {block['tokens']['mean']:.2f} |"
                )
    lines.extend(
        [
            "",
            "Pass rate is passed heuristics plus rubric items over all of those checks. "
            "Delta is with_skill minus without_skill (baseline). Stddev needs more than "
            "one row per config; use `--repeats` for run-to-run spread.",
            "",
            "| Case | Arm | Repeat | Heuristics | Judge | Score | Status |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['case']} | {row['arm']} | {row['repeat']} | {row['heuristic_ok']} | "
            f"{row['judge_pass'] or 'n/a'} | {row['judge_score'] or 'n/a'} | {row['status']} |"
        )
    for row in rows:
        answer = f"{row['case']}-{row['arm']}-{row['repeat']}.txt"
        lines.extend(
            [
                "",
                f"## {row['case']} / {row['arm']} / {row['repeat']}",
                "",
                f"- Status: {row['status']}",
                f"- Heuristic fails: {row['heuristic_fails'] or 'none'}",
                f"- Judge fails: {row['judge_fails'] or 'none'}",
                f"- Evidence: {row['evidence'] or 'none'}",
                f"- Error: {row['error'] or 'none'}",
                f"- Duration: {row['duration_ms']} ms; tokens in/out: "
                f"{row['input_tokens'] or 'n/a'}/{row['output_tokens'] or 'n/a'}",
                f"- Answer: [{answer}](./{answer})",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
