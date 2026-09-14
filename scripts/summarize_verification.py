"""Summarize catalog verification without machine or run identifiers."""

import json
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]


def main():
    evidence = ROOT / "evidence"
    result = {"scope": "Fictional inventory; aggregate verification results only"}
    junit = evidence / "unit-tests.xml"
    if junit.exists():
        suites = list(ElementTree.parse(junit).iter("testsuite"))
        result["python_tests"] = {key: sum(int(s.attrib.get(key, 0)) for s in suites) for key in ["tests", "failures", "errors", "skipped"]}
    integration = evidence / "integration.json"
    if integration.exists():
        result["integration_checks"] = json.loads(integration.read_text())["checks"]
    (evidence / "verification-summary.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
