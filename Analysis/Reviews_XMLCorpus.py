#!/usr/bin/env python3
"""Export the full review corpus and four rating subsets as well-formed XML.

Run: python3 Analysis/Reviews_XMLCorpus.py (standard library only).
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
INVALID_XML = re.compile(r"[^\x09\x0a\x0d\x20-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]")
GROUPS = {1: "low", 2: "low", 3: "middle", 4: "high", 5: "high", None: "no_rating"}


def build_corpus(rows):
    """Validate source records and create documents in source order."""
    if not isinstance(rows, list) or not rows or not all(isinstance(row, dict) for row in rows):
        raise ValueError("Expected a nonempty JSON array of review objects.")
    corpus = ET.Element("corpus")
    seen = set()
    counts = Counter()
    removed = 0
    for row in rows:
        review_id = str(row["index"])
        if review_id in seen:
            raise ValueError(f"Duplicate source index: {review_id}")
        seen.add(review_id)
        reviewer = re.search(r"/user/show/(\d+)", row.get("reviewer_url") or "")
        if reviewer is None:
            raise ValueError(f"Missing reviewer ID at index {review_id}")
        rating = row["rating"]
        if isinstance(rating, bool) or rating not in GROUPS:
            raise ValueError(f"Unexpected rating at index {review_id}: {rating!r}")
        if not isinstance(row["text"], str):
            raise ValueError(f"Missing review text at index {review_id}")
        attributes = {
            "review_id": review_id,
            "book_id": str(row["book_id"]),
            "reviewer_id": reviewer.group(1),
            "rating": "" if rating is None else str(int(rating)),
            "rating_group": GROUPS[rating],
        }
        if any(INVALID_XML.search(value) for value in attributes.values()):
            raise ValueError(f"Invalid XML character in metadata at index {review_id}")
        text, n = INVALID_XML.subn("", row["text"])
        removed += n
        doc = ET.SubElement(corpus, "doc", attributes)
        doc.text = text
        doc.tail = "\n"
        counts[GROUPS[rating]] += 1
    corpus.text = "\n"
    return corpus, counts, removed


def serialize_corpus(corpus):
    """Escape XML markup and verify that metadata and text round-trip exactly."""
    # ElementTree escapes markup characters without deleting meaningful symbols.
    # Encode CR explicitly to prevent XML parsers normalizing it to LF.
    xml = ET.tostring(corpus, encoding="utf-8", xml_declaration=True).replace(b"\r", b"&#13;")
    parsed = ET.fromstring(xml)
    if len(parsed) != len(corpus):
        raise ValueError("XML review count mismatch.")
    for expected, actual in zip(corpus, parsed):
        if expected.attrib != actual.attrib or (expected.text or "") != (actual.text or ""):
            raise ValueError("XML round-trip mismatch.")
    return xml + b"\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "Data/Reviews/AllReviews_217_VA.json")
    parser.add_argument("--output", type=Path, default=ROOT / "Data/Reviews/XML/AllReviews_217_VA.xml",
                        help="Full-corpus XML path; rating XML files are written beside it.")
    args = parser.parse_args()
    source = args.input.read_bytes()
    corpus, counts, removed = build_corpus(json.loads(source))
    exports = {args.output: corpus}
    for group in ("high", "low", "middle", "no_rating"):
        filename = "no_rating.xml" if group == "no_rating" else f"{group}_rating.xml"
        path = args.output.parent / filename
        if path.resolve() == args.output.resolve():
            raise ValueError("Full-corpus filename must differ from rating-subset filenames.")
        subset = ET.Element("corpus")
        subset.text = "\n"
        subset.extend(doc for doc in corpus if doc.attrib["rating_group"] == group)
        exports[path] = subset
    if any(path.resolve() == args.input.resolve() for path in exports):
        raise ValueError("Output must not overwrite the source.")
    # Prepare and validate all five exports before writing any output.
    payloads = {path: serialize_corpus(tree) for path, tree in exports.items()}
    if args.input.read_bytes() != source:
        raise ValueError("Source changed during export.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for path, payload in payloads.items():
        path.write_bytes(payload)
        if path.read_bytes() != payload:
            raise ValueError(f"Written XML differs from validated content: {path}")
    print(json.dumps({"outputs": {str(path): len(tree) for path, tree in exports.items()},
                      "rating_groups": counts, "invalid_xml_characters_removed": removed,
                      "source_sha256": hashlib.sha256(source).hexdigest(),
                      "xml_round_trip_verified": True}, indent=2))


if __name__ == "__main__":
    main()
