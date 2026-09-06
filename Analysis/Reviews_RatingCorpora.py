#!/usr/bin/env python3
"""Partition the VA corpus by recovered star rating; preserve all source fields.

Reuses the descriptive analysis metadata join (requires NumPy and Matplotlib).
Run: python3 Analysis/Reviews_RatingCorpora.py
"""

import argparse
import hashlib
import json
from pathlib import Path

from Reviews_DescriptiveAnalysis import (
    DEFAULT_INPUT, DEFAULT_REVIEW_METADATA_CANDIDATES,
    DEFAULT_BOOK_METADATA_CANDIDATES, PROJECT_ROOT,
    enrich_records, first_existing, load_records,
)


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
    parser.add_argument("--review-metadata", type=Path,
                        default=first_existing(DEFAULT_REVIEW_METADATA_CANDIDATES))
    parser.add_argument("--book-metadata", type=Path,
                        default=first_existing(DEFAULT_BOOK_METADATA_CANDIDATES))
    parser.add_argument("--output", type=Path,
                        default=PROJECT_ROOT / "Data/Reviews/Rating")
    args = parser.parse_args()
    if args.review_metadata is None or args.book_metadata is None:
        parser.error("Original review and book metadata are required to recover ratings.")

    sources = {name: fingerprint(path) for name, path in (
        ("input", args.input), ("review_metadata", args.review_metadata),
        ("book_metadata", args.book_metadata))}
    originals = load_records(args.input)
    by_index = {row["index"]: row for row in originals}
    if len(by_index) != len(originals):
        raise ValueError("Source indexes must be unique.")
    enriched, join_audit, _ = enrich_records(
        originals, args.review_metadata, args.book_metadata)
    groups = {name: [] for name in GROUPS}
    for row in enriched:
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
                "metadata_join_audit": join_audit, "corpora": summaries,
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
              "The VA source has no rating field. Ratings were recovered using `enrich_records` from `Analysis/Reviews_DescriptiveAnalysis.py`, the same join used for the descriptive results. Source paths, SHA-256 hashes, and the join audit are recorded in `manifest.json`.", "",
              "Matching uses book ID, exact review text, likes, shelves, and stored word count. Duplicate composite keys consume source metadata rows once each in source order. This preserves the metadata multiset, but individual source-index assignments within indistinguishable duplicate groups are ambiguous; see the join audit.", "",
              "All eight original fields are preserved. Added fields are `rating`, `review_date`, and the deterministic pseudonymous `reviewer_id`. Missing ratings are JSON `null`; unexpected rating values cause an error. Original index values and within-group source order are retained.", "",
              "Every source review occurs in exactly one corpus. No sampling, deduplication, length filtering, or text preprocessing was applied. Three stars means middle-rated, not necessarily neutral textual evaluation. Word totals use the existing `word_count` field, not a new tokenizer.", "",
              "## Reproduction", "",
              "Run from the repository root (Python, NumPy, and Matplotlib required by the reused analysis module):", "",
              "```sh", "python3 Analysis/Reviews_RatingCorpora.py", "```", "",
              "Use `--input`, `--review-metadata`, `--book-metadata`, and `--output` to override paths. Default metadata discovery includes the sibling private project, so another checkout may need explicit metadata paths. Re-running replaces these derived outputs. Original data is never modified.", "",
              "Validation checks exhaustive and disjoint membership, preservation of original fields, JSON read-back, and unchanged source hashes."]
    (args.output / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
