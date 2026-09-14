"""Remove the local hostname from the public JUnit report."""

from pathlib import Path
from xml.etree import ElementTree


def main():
    path = Path(__file__).resolve().parents[1] / "evidence/unit-tests.xml"
    if path.exists():
        tree = ElementTree.parse(path)
        for element in tree.iter():
            element.attrib.pop("hostname", None)
        tree.write(path, encoding="unicode", xml_declaration=True)


if __name__ == "__main__":
    main()
