#!/usr/bin/env python3
"""Partition the VA corpus by its stored star rating; preserve all source fields.

Requires only the Python standard library.
Run: python3 Analysis/Reviews_RatingCorpora.py
"""

import argparse
import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = PROJECT_ROOT / 'Data/Reviews/AllReviews_217_VA.json'


GROUPS = {
    "high_rating": (4, 5),
    "low_rating": (1, 2),
    "middle_rating": (3,),
    "no_rating": (None,),
}


def fingerprint(path):
    return {"path": str(path.resolve()),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path,
                        default=PROJECT_ROOT / "Data/Reviews/Rating")
    args = parser.parse_args()
    sources = {"input": fingerprint(args.input)}
    originals = json.loads(args.input.read_text(encoding='utf-8'))
    if not isinstance(originals, list) or not originals or not all(isinstance(r, dict) and 'rating' in r for r in originals):
        raise ValueError('Expected a nonempty JSON array with a rating field on every record.')
    by_index = {row["index"]: row for row in originals}
    if len(by_index) != len(originals):
        raise ValueError("Source indexes must be unique.")
    groups = {name: [] for name in GROUPS}
    for row in originals:
        rating = row["rating"]
        if rating is not None and (isinstance(rating, bool) or rating not in (1, 2, 3, 4, 5)):
            raise ValueError(f"Invalid rating at source index {row['index']}: {rating!r}")
        for name, ratings in GROUPS.items():
            if rating in ratings:
                groups[name].append(row)
                break

    # Validate complete, disjoint membership and unchanged source fields before writing.
    flattened = [row for rows in groups.values() for row in rows]
    indexes = [row["index"] for row in flattened]
    if len(indexes) != len(originals) or len(set(indexes)) != len(indexes) or set(indexes) != set(by_index):
        raise ValueError("Partition must contain every source index exactly once.")
    for row in flattened:
        if any(row[key] != value for key, value in by_index[row["index"]].items()):
            raise ValueError(f"Source fields changed at index {row['index']}.")

    targets = [args.output / f"{name}.json" for name in GROUPS]
    targets += [args.output / "manifest.json", args.output / "README.md"]
    source_paths = {Path(value["path"]) for value in sources.values()}
    if any(path.resolve() in source_paths for path in targets):
        raise ValueError("Output cannot overwrite a source file.")
    args.output.mkdir(parents=True, exist_ok=True)
    summaries = []
    for name, rows in groups.items():
        path = args.output / f"{name}.json"
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                        encoding="utf-8")
        if json.loads(path.read_text(encoding="utf-8")) != rows:
            raise ValueError(f"Round-trip verification failed: {path}")
        summaries.append({"file": path.name, "ratings": GROUPS[name],
                          "reviews": len(rows), "books": len({r['id'] for r in rows}),
                          "stored_word_count": sum(r["word_count"] for r in rows),
                          "sha256": fingerprint(path)["sha256"]})
    for name, info in sources.items():
        if fingerprint(Path(info["path"])) != info:
            raise ValueError(f"Source changed during execution: {name}")
    manifest = {"sources": sources, "source_review_count": len(originals),
                "rating_source": "embedded input rating field; no metadata join", "corpora": summaries,
                "validation": {"complete_disjoint_partition": True,
                               "original_fields_preserved": True,
                               "json_round_trip_verified": True,
                               "sources_unchanged": True}}
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Rating sub-corpora", "",
             "Derived from `Data/Reviews/AllReviews_217_VA.json`. Each file is a UTF-8 JSON array, matching the source format.", "",
             "| File | Ratings | Reviews | Books | Stored words |",
             "|---|---|---:|---:|---:|"]
    for item in summaries:
        ratings = ", ".join("missing (null)" if r is None else str(r) for r in item["ratings"])
        lines.append(f"| {item['file']} | {ratings} | {item['reviews']:,} | {item['books']} | {item['stored_word_count']:,} |")
    lines += ["", "## Preparation and provenance", "",
              "Ratings are read directly from the current input JSON. No metadata join is performed. Source paths and SHA-256 hashes are recorded in `manifest.json`.", "",
              "All original fields and values are preserved, including reviewer names and URLs. No fields are added. Missing ratings are JSON `null`; absent rating fields and unexpected values cause an error. Original indexes and within-group source order are retained.", "",
              "Every source review occurs in exactly one corpus. No sampling, deduplication, length filtering, or text preprocessing was applied. Three stars means middle-rated, not necessarily neutral textual evaluation. Word totals use the existing `word_count` field, not a new tokenizer.", "",
              "## Reproduction", "",
              "Run from the repository root (Python standard library only):", "",
              "```sh", "python3 Analysis/Reviews_RatingCorpora.py", "```", "",
              "Use `--input` and `--output` to override paths. Re-running replaces these derived outputs. Original data is never modified.", "",
              "Validation checks exhaustive and disjoint membership, preservation of original fields, JSON read-back, and unchanged source hashes."]
    (args.output / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
