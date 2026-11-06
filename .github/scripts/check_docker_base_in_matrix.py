#!/usr/bin/env python3
"""Assert the production image's Python base is an interpreter the test matrix covers.

Why this exists: the Dockerfile base and the CI matrix drift apart silently. The test job
installs its own interpreter with actions/setup-python, and the image is only built on
`main`, so a `build(deps)` bump of `FROM python:3.13-slim` to `python:3.15-slim` landed with
every check green while production moved to an interpreter no test leg had ever executed.

The rule enforced here: every Python minor the image ships must appear in
`.github/workflows/ci.yml`'s `matrix.python-version`, so "the image claims version X" is
always backed by a leg that runs on X.

Exit codes
    0  the image base is covered by the matrix
    1  the image base is NOT covered (the defect this guards)
    2  undeterminable (no python FROM, no matrix, unparsable tag) - also a failure, so a
       scan that could not measure can never report an all-clear
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

FROM_RE = re.compile(r"^\s*FROM\s+(?:--platform=\S+\s+)?(?P<image>\S+)", re.IGNORECASE)
PYTHON_IMAGE_RE = re.compile(r"^(?:docker\.io/)?(?:library/)?python:(?P<tag>[\w.\-]+)$")
MINOR_RE = re.compile(r"^(?P<minor>\d+\.\d+)")
MATRIX_INLINE_RE = re.compile(r"^\s*python-version:\s*\[(?P<items>[^\]]*)\]")
MATRIX_BLOCK_RE = re.compile(r"^\s*python-version:\s*$")
MATRIX_ITEM_RE = re.compile(r"^\s*-\s*['\"]?(?P<ver>\d+(?:\.\d+)+)['\"]?\s*$")


def image_python_bases(dockerfile_text: str) -> list[tuple[int, str, str]]:
    """(line_no, image, minor) for every python FROM, in file order."""
    out = []
    for i, line in enumerate(dockerfile_text.splitlines(), 1):
        m = FROM_RE.match(line)
        if not m:
            continue
        pm = PYTHON_IMAGE_RE.match(m.group("image"))
        if not pm:
            continue
        tag = pm.group("tag")
        mm = MINOR_RE.match(tag)
        out.append((i, m.group("image"), mm.group("minor") if mm else ""))
    return out


def ci_matrix(ci_text: str) -> list[str]:
    """Python versions listed in the workflow's matrix, inline or block form."""
    lines = ci_text.splitlines()
    found = []
    for i, line in enumerate(lines):
        inline = MATRIX_INLINE_RE.match(line)
        if inline:
            for item in inline.group("items").split(","):
                ver = item.strip().strip("'\"")
                if ver:
                    found.append(ver)
            continue
        if MATRIX_BLOCK_RE.match(line):
            indent = len(line) - len(line.lstrip())
            for nxt in lines[i + 1:]:
                if nxt.strip() and (len(nxt) - len(nxt.lstrip())) <= indent:
                    break
                item = MATRIX_ITEM_RE.match(nxt)
                if item:
                    found.append(item.group("ver"))
    return found


def minor_of(version: str) -> str:
    return ".".join(version.split(".")[:2])


def check(dockerfile_text: str, ci_text: str) -> tuple[int, list[str]]:
    """Return (exit_code, message lines)."""
    msg = []
    bases = image_python_bases(dockerfile_text)
    matrix = ci_matrix(ci_text)
    if not bases:
        return 2, ["ERROR: no `FROM python:<version>` line in the Dockerfile - cannot verify."]
    if not matrix:
        return 2, ["ERROR: no `matrix.python-version` list in the CI workflow - cannot verify."]

    msg.append("Dockerfile python base(s): " + ", ".join(f"{img} (line {ln})" for ln, img, _ in bases))
    msg.append("CI test matrix:            " + ", ".join(matrix))

    runtime_ln, runtime_img, runtime_minor = bases[-1]
    if len(bases) > 1:
        msg.append(f"NOTE: {len(bases)} python stages; the last one (line {runtime_ln}) ships.")
    if not runtime_minor:
        return 2, msg + [f"ERROR: cannot read a Python minor from `{runtime_img}`."]

    covered = {minor_of(v) for v in matrix}
    if runtime_minor in covered:
        msg.append(f"OK: runtime base {runtime_minor} is covered by the test matrix.")
        return 0, msg
    msg.append(
        f"FAIL: runtime base python:{runtime_minor} is NOT in the test matrix "
        f"({', '.join(matrix)}). Production would run an interpreter no leg tests."
    )
    msg.append(
        "Fix one of: pin the image to a matrix version, or add the version to "
        "`.github/workflows/ci.yml` -> jobs.test.strategy.matrix.python-version (and keep the "
        "leg blocking - never allow_failure)."
    )
    return 1, msg


SELF_TEST_CASES = [
    ("covered", "FROM python:3.13-slim\n", "      python-version: ['3.13', '3.14']\n", 0),
    ("drifted", "FROM python:3.15-slim\n", "      python-version: ['3.13', '3.14']\n", 1),
    ("block list", "FROM python:3.14-slim-bookworm\n",
     "        python-version:\n          - '3.13'\n          - '3.14'\n", 0),
    ("stage, last wins", "FROM python:3.15-slim AS builder\nFROM python:3.13-slim\n",
     "      python-version: ['3.13', '3.14']\n", 0),
    ("no python base", "FROM debian:bookworm\n", "      python-version: ['3.13']\n", 2),
    ("no matrix", "FROM python:3.13-slim\n", "name: CI\n", 2),
    ("unpinned tag", "FROM python:latest\n", "      python-version: ['3.13']\n", 2),
]


def self_test() -> int:
    failures = 0
    for name, dockerfile, ci, expected in SELF_TEST_CASES:
        code, _msg = check(dockerfile, ci)
        ok = code == expected
        failures += 0 if ok else 1
        print(f"  {'ok  ' if ok else 'FAIL'} {name}: expected rc={expected}, got rc={code}")
    print(f"self-test: {len(SELF_TEST_CASES) - failures}/{len(SELF_TEST_CASES)} passed")
    return 0 if failures == 0 else 1


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    dockerfile = REPO_ROOT / "Dockerfile"
    ci_file = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    for path in (dockerfile, ci_file):
        if not path.exists():
            print(f"ERROR: {path} not found (cannot verify).")
            return 2
    code, lines = check(dockerfile.read_text(encoding="utf-8"), ci_file.read_text(encoding="utf-8"))
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
