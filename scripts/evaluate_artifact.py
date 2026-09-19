#!/usr/bin/env python3
"""Record repeatable agent-evaluation evidence; editorial scores require human review."""
import argparse, hashlib, json, re, sys
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.text = []

    def handle_starttag(self, t, a):
        if t in ("script", "style"):
            self.skip += 1

    def handle_endtag(self, t):
        if t in ("script", "style"):
            self.skip = max(0, self.skip - 1)

    def handle_data(self, s):
        if not self.skip:
            self.text.append(s)


p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--case", required=True)
p.add_argument("--artifact", type=Path, required=True)
p.add_argument("--agent", required=True)
p.add_argument("--model", required=True)
p.add_argument("--output", type=Path, required=True)
a = p.parse_args()
cases = json.loads((ROOT / "tests/fixtures/agent-evaluation/cases.json").read_text())[
    "cases"
]
case = next((c for c in cases if c["id"] == a.case), None)
if not case:
    raise SystemExit("Unknown evaluation case")
content = a.artifact.read_text()
text = Text()
text.feed(content)
visible = " ".join(text.text)
checks = {
    "stable_identity": bool(
        re.search(
            r"name=[\"\']nota-documento[\"\']\s+content=[\"\']"
            + re.escape(case["document_id"])
            + r"[\"\']",
            content,
        )
    ),
    "required_evidence_present": all(t in visible for t in case["required_terms"]),
    "responsive_viewport": bool(re.search(r"name=[\"\']viewport[\"\']", content)),
}
result = {
    "schema": 1,
    "case": case,
    "agent": a.agent,
    "model": a.model,
    "skill_version": json.loads((ROOT / "VERSION.json").read_text())["version"],
    "sha256": hashlib.sha256(content.encode()).hexdigest(),
    "automated_checks": checks,
    "human_review": {
        k: None
        for k in [
            "factual_grounding",
            "voice",
            "useful_components",
            "mobile_and_keyboard",
            "privacy",
            "format_preservation",
            "actionability",
        ]
    },
    "status": "requires-human-review",
}
a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(a.output)
sys.exit(0 if all(checks.values()) else 1)
