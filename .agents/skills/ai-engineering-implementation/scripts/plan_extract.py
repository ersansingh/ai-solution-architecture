#!/usr/bin/env python3
"""Read an Engineering Implementation Plan (Markdown) and produce work orders or a trace report.

Subcommands
  workorders PLAN [-o FILE] [--format md|json] [--milestone M2]
      Extract tasks, requirements, tests, ADRs, open decisions, interfaces and
      components from the plan's tables and group the tasks by owner role.
  trace PLAN IMPL_DIR [-o FILE] [--format md|json]
      Check that every requirement ID and test ID in the plan appears somewhere
      in the implementation (source, tests, docs, workflows). Reports only ID
      presence, never whether the test is any good: a human or the reviewer
      must still read it.

The parser is deliberately simple: it reads Markdown pipe tables and classifies a
row by the ID in its first cell. Standard library only. Run with: python -I <this file> ...
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ID_PATTERNS = {
    "task": re.compile(r"^M\d+-\d+$"),
    "test": re.compile(r"^T-\d+$"),
    "requirement": re.compile(r"^(BR|FR|NFR|REG|GR|AC|KPI)-?\d+$", re.I),
    "adr": re.compile(r"^ADR-\d+$"),
    "decision": re.compile(r"^OD-\d+$"),
    "risk": re.compile(r"^R\d+$"),
}
ID_IN_TEXT = re.compile(r"\b(?:BR|FR|NFR|REG|GR|AC|KPI)-?\d+\b|\bT-\d+\b|\bADR-\d+\b|\bOD-\d+\b", re.I)
SCAN_SUFFIXES = {".py", ".md", ".yml", ".yaml", ".json", ".tf", ".toml", ".txt", ".sh", ".ps1", ".cfg", ".ini", ".ts", ".js", ".sql"}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".terraform", ".mypy_cache", ".pytest_cache", ".ruff_cache"}


def split_row(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    cells, cur, in_code = [], [], False
    for i, ch in enumerate(body):
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code and (i == 0 or body[i - 1] != "\\"):
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    cells.append("".join(cur).strip())
    return cells


def parse_tables(text: str):
    """Yield (section_heading, milestone_heading, header, rows) for each pipe table."""
    section, milestone = "", ""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            section = heading
            if re.match(r"^M\d+\b", heading):
                milestone = heading.split()[0]
        if line.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            header, seen = [], {}
            for name in split_row(line):  # duplicate column names must not collapse into one key
                seen[name] = seen.get(name, 0) + 1
                header.append(name if seen[name] == 1 else f"{name} ({seen[name]})")
            rows = []
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                cells = split_row(lines[i])
                if len(cells) < len(header):
                    cells += [""] * (len(header) - len(cells))
                rows.append(dict(zip(header, cells)))
                i += 1
            yield section, milestone, header, rows
            continue
        i += 1


def clean_id(cell: str) -> str:
    return re.sub(r"[`*_ ]", "", cell)


def extract(plan_path: Path) -> dict:
    text = plan_path.read_text(encoding="utf-8")
    out = {"plan": str(plan_path), "tasks": [], "requirements": [], "tests": [], "adrs": [],
           "decisions": [], "risks": [], "interfaces": [], "components": []}
    for section, milestone, header, rows in parse_tables(text):
        first = header[0] if header else ""
        for row in rows:
            rid = clean_id(row.get(first, ""))
            kind = next((k for k, pat in ID_PATTERNS.items() if pat.match(rid)), None)
            if kind == "task":
                out["tasks"].append({"id": rid, "milestone": milestone or rid.split("-")[0], "row": row})
            elif kind == "requirement":
                out["requirements"].append({"id": rid.upper(), "section": section, "row": row})
            elif kind == "test":
                out["tests"].append({"id": rid, "row": row})
            elif kind == "adr":
                out["adrs"].append({"id": rid, "row": row})
            elif kind == "decision":
                out["decisions"].append({"id": rid, "row": row})
            elif kind == "risk":
                out["risks"].append({"id": rid, "row": row})
        if section.startswith("6.") or section.startswith("6 ") or "Component Build Specs" in section:
            out["components"].extend(rows)
        if section.startswith("8.") or section.startswith("8 ") or "Interfaces and Contracts" in section:
            out["interfaces"].extend(rows)
    return out


def owner_of(task: dict) -> str:
    row = task["row"]
    for key, val in row.items():
        if key.lower().startswith("owner"):
            return val.lower()
    return ""


def role_bucket(owner: str) -> str:
    o = owner.lower()
    if "devops" in o or "sre" in o or "platform" in o:
        return "devops"
    if "test" in o or "qa" in o or "sdet" in o:
        return "tester"
    if "dev" in o or "backend" in o or "eng" in o:
        return "developer"
    if "data" in o or "ml" in o or "ai" in o:
        return "data/ai"
    return "other (business / PM / unassigned)"


def render_workorders(data: dict, milestone: str | None) -> str:
    tasks = [t for t in data["tasks"] if not milestone or t["milestone"] == milestone]
    buckets: dict[str, list] = {}
    for t in tasks:
        buckets.setdefault(role_bucket(owner_of(t)), []).append(t)
    lines = [f"# Work orders from `{data['plan']}`", "",
             f"Tasks: {len(tasks)} · Requirements: {len(data['requirements'])} · Tests: {len(data['tests'])} · "
             f"ADRs: {len(data['adrs'])} · Open decisions: {len(data['decisions'])} · Components: {len(data['components'])} · "
             f"Interfaces: {len(data['interfaces'])}", ""]
    if milestone:
        lines += [f"Filtered to milestone **{milestone}**.", ""]
    for bucket in ("developer", "tester", "devops", "data/ai", "other (business / PM / unassigned)"):
        items = buckets.get(bucket)
        if not items:
            continue
        lines += [f"## {bucket} ({len(items)} tasks)", "", "| Task | Milestone | Task text | Owner (as written) | Depends | Ref | Done when |",
                  "| :-: | :-: | :--- | :-: | :-: | :-: | :--- |"]
        for t in items:
            r = t["row"]

            def pick(*prefixes):
                for k, v in r.items():
                    if any(k.lower().startswith(p) for p in prefixes):
                        return v.replace("|", "/")
                return ""
            lines.append(f"| {t['id']} | {t['milestone']} | {list(r.values())[1].replace('|', '/')} | "
                         f"{pick('owner')} | {pick('depend')} | {pick('ref')} | {pick('done')} |")
        lines.append("")
    if not tasks:
        lines.append("No task rows matched (expected IDs like `M0-01` in the first column of a table).")
    return "\n".join(lines) + "\n"


def scan_ids(impl_dir: Path) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for p in impl_dir.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in SCAN_SUFFIXES or any(part in SKIP_DIRS for part in p.parts):
            continue
        try:
            body = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in ID_IN_TEXT.findall(body):
            found.setdefault(m.upper().replace("_", "-"), set()).add(str(p.relative_to(impl_dir)))
    return found


def trace(data: dict, impl_dir: Path) -> dict:
    found = scan_ids(impl_dir)
    test_files = {k: v for k, v in found.items()}

    def where(i):
        return sorted(test_files.get(i.upper(), []))
    rows = {"requirements": [], "tests": []}
    for kind in ("requirements", "tests"):
        for item in data[kind]:
            files = where(item["id"])
            rows[kind].append({"id": item["id"], "files": files, "covered": bool(files)})
    return rows


def render_trace(rows: dict, plan: str, impl: str) -> str:
    lines = [f"# ID trace: `{plan}` vs `{impl}`", "",
             "Presence of an ID in a file is **evidence to look at, not proof of coverage**. Read the test before crediting it.", ""]
    for kind in ("requirements", "tests"):
        miss = [r for r in rows[kind] if not r["covered"]]
        lines += [f"## {kind.capitalize()}: {len(rows[kind]) - len(miss)}/{len(rows[kind])} referenced", "",
                  "| ID | Found in | Status |", "| :-: | :--- | :-: |"]
        for r in rows[kind]:
            where = ", ".join(f"`{f}`" for f in r["files"][:4]) + (" ..." if len(r["files"]) > 4 else "")
            lines.append(f"| {r['id']} | {where or '-'} | {'ok' if r['covered'] else '**MISSING**'} |")
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("workorders")
    w.add_argument("plan", type=Path)
    w.add_argument("-o", "--output", type=Path)
    w.add_argument("--format", choices=["md", "json"], default="md")
    w.add_argument("--milestone")
    t = sub.add_parser("trace")
    t.add_argument("plan", type=Path)
    t.add_argument("impl_dir", type=Path)
    t.add_argument("-o", "--output", type=Path)
    t.add_argument("--format", choices=["md", "json"], default="md")
    args = ap.parse_args(argv)

    if not args.plan.is_file():
        print(f"error: plan not found: {args.plan}", file=sys.stderr)
        return 2
    data = extract(args.plan)
    if args.cmd == "workorders":
        result = json.dumps(data, indent=2, ensure_ascii=False) if args.format == "json" else render_workorders(data, args.milestone)
    else:
        if not args.impl_dir.is_dir():
            print(f"error: implementation dir not found: {args.impl_dir}", file=sys.stderr)
            return 2
        rows = trace(data, args.impl_dir)
        result = json.dumps(rows, indent=2) if args.format == "json" else render_trace(rows, str(args.plan), str(args.impl_dir))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        sys.stdout.buffer.write(result.encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
