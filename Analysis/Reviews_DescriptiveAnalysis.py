#!/usr/bin/env python3
"""Reproducible descriptive analysis of AllReviews_217_VA.json.

The script uses only the Python standard library, NumPy, and Matplotlib. It
validates the record structure; summarizes numeric fields, books, and shelves;
checks duplicate text; and calculates correlations. When the original review
and book metadata are available, it also analyzes star ratings, rating/valence
agreement, book effects, reviewer concentration, high/low corpora, and dates.
It writes all tables, figures, and its Markdown report under Results/ by default.

Run from any directory:
    python Analysis/Reviews_DescriptiveAnalysis.py

Optional paths:
    python Analysis/Reviews_DescriptiveAnalysis.py --input PATH --output DIR \
        --review-metadata REVIEWS.ndjson --book-metadata BOOKS.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict, deque
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parent.parent
DEFAULT_INPUT = PROJECT_ROOT / "Data" / "Reviews" / "AllReviews_217_VA.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "Results" / "Reviews_DescriptiveResults"
SIBLING_PROJECT = PROJECT_ROOT.parent / PROJECT_ROOT.name.removesuffix("_public")
DEFAULT_REVIEW_METADATA_CANDIDATES = (
    PROJECT_ROOT / "Data" / "Reviews" / "AllReviews_217_Metadata.ndjson",
    SIBLING_PROJECT / "Data" / "Reviews_Scraped" / "temp_all_reviews.json",
    SIBLING_PROJECT / "Data" / "Temp" / "temp_all_reviews.ndjson",
)
DEFAULT_BOOK_METADATA_CANDIDATES = (
    PROJECT_ROOT / "Data" / "Goodreads_Comics_Data" / "Data_Files" / "book_metadata.csv",
    SIBLING_PROJECT / "Data" / "Temp" / "temp_book_sheet.csv",
)
EXPECTED_FIELDS = (
    "index",
    "id",
    "text",
    "likes",
    "shelves",
    "word_count",
    "valence",
    "arousal",
)
NUMERIC_FIELDS = ("likes", "word_count", "valence", "arousal")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--review-metadata", type=Path, default=first_existing(DEFAULT_REVIEW_METADATA_CANDIDATES),
        help="NDJSON with rating, reviewer_url, review_date, and review_text fields.",
    )
    parser.add_argument(
        "--book-metadata", type=Path, default=first_existing(DEFAULT_BOOK_METADATA_CANDIDATES),
        help="CSV mapping numeric book_id to goodreads_id and publication_date.",
    )
    return parser.parse_args()


def first_existing(paths: Sequence[Path]) -> Path | None:
    return next((path for path in paths if path.is_file()), None)


def local_book_metadata():
    """Read BOOK_SHEET from the local 225-book workbook (standard library only)."""
    from zipfile import ZipFile
    from xml.etree import ElementTree as ET
    path = PROJECT_ROOT / 'Data/Goodreads_Comics_Data/Data_Files/Masterdata_ongoing_225.xlsx'
    ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    with ZipFile(path) as archive:
        strings = [''.join(t.text or '' for t in si.iter(ns + 't'))
                   for si in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        sheet = next(s for s in workbook.find(ns + 'sheets') if s.attrib['name'] == 'BOOK_SHEET')
        rel_id = sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
        rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        target = next(r.attrib['Target'] for r in rels if r.attrib['Id'] == rel_id)
        target = target.lstrip('/') if target.startswith('/') else 'xl/' + target
        rows = []
        for row in ET.fromstring(archive.read(target)).iter(ns + 'row'):
            cells = {}
            for cell in row:
                column = ''.join(c for c in cell.attrib['r'] if c.isalpha())
                value = cell.find(ns + 'v')
                value = value.text if value is not None else ''
                if cell.attrib.get('t') == 's':
                    value = strings[int(value)]
                elif cell.attrib.get('t') == 'inlineStr':
                    value = ''.join(t.text or '' for t in cell.iter(ns + 't'))
                cells[column] = value
            rows.append(cells)
    headers = rows[0]
    records = [{headers[k]: v for k, v in row.items() if k in headers} for row in rows[1:]]
    books = {r['goodreads_id']: r for r in records if r.get('goodreads_id')}
    if len(books) != len(records):
        raise ValueError('Duplicate or missing Goodreads IDs in book metadata')
    return path, books


def load_records(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise ValueError("Expected the JSON top level to be a list of objects.")
    if not data:
        raise ValueError("The input dataset is empty.")
    return data


def load_ndjson(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid NDJSON at {path}:{line_number}: {error}") from error
            if not isinstance(record, dict):
                raise ValueError(f"Expected an object at {path}:{line_number}.")
            records.append(record)
    return records


def load_book_metadata(path: Path) -> tuple[dict[int, dict[str, str]], dict[str, dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"book_id", "goodreads_id", "publication_date"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"Book metadata must contain {sorted(required)}: {path}")
    by_numeric_id = {int(row["book_id"]): row for row in rows if row.get("book_id")}
    by_goodreads_id = {row["goodreads_id"]: row for row in rows if row.get("goodreads_id")}
    return by_numeric_id, by_goodreads_id


def review_join_key(record: dict[str, Any], goodreads_id: str, source: bool) -> tuple[Any, ...]:
    return (
        goodreads_id,
        record.get("review_text" if source else "text"),
        record.get("likes"),
        tuple(record.get("shelves") or []),
        record.get("word_count"),
    )


def pseudonymous_reviewer_id(reviewer_url: str) -> str:
    digest = hashlib.sha256(reviewer_url.encode("utf-8")).hexdigest()[:16]
    return f"reviewer_{digest}"


def enrich_records(
    records: list[dict[str, Any]],
    review_metadata_path: Path,
    book_metadata_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, dict[str, str]]]:
    """Join review metadata without relying on row order.

    Matching uses book ID, exact review text, likes, shelves, and word count. For
    indistinguishable duplicate keys, source rows are consumed once each. This
    preserves the metadata multiset; duplicate texts have identical VA scores.
    """
    source_records = load_ndjson(review_metadata_path)
    books_by_number, books_by_goodreads = load_book_metadata(book_metadata_path)
    buckets: dict[tuple[Any, ...], deque[dict[str, Any]]] = defaultdict(deque)
    source_with_text = 0
    unmapped_source_books = 0
    for source_record in source_records:
        book = books_by_number.get(int(source_record["book_id"]))
        if book is None:
            unmapped_source_books += 1
            continue
        if source_record.get("review_text") is None:
            continue
        source_with_text += 1
        key = review_join_key(source_record, book["goodreads_id"], source=True)
        buckets[key].append(source_record)

    duplicate_source_keys = sum(len(group) > 1 for group in buckets.values())
    duplicate_source_rows = sum(len(group) for group in buckets.values() if len(group) > 1)
    enriched = []
    unmatched_indexes = []
    for record in records:
        key = review_join_key(record, record["id"], source=False)
        if not buckets[key]:
            unmatched_indexes.append(record["index"])
            continue
        source_record = buckets[key].popleft()
        merged = dict(record)
        merged.update(
            {
                "rating": source_record.get("rating"),
                "review_date": source_record.get("review_date"),
                "reviewer_id": pseudonymous_reviewer_id(source_record.get("reviewer_url", "")),
            }
        )
        enriched.append(merged)

    unused_source_rows = sum(len(group) for group in buckets.values())
    diagnostics = {
        "va_review_count": len(records),
        "source_review_count": len(source_records),
        "source_reviews_with_text": source_with_text,
        "matched_review_count": len(enriched),
        "unmatched_va_review_count": len(unmatched_indexes),
        "unused_source_reviews_with_text": unused_source_rows,
        "source_reviews_without_text": len(source_records) - source_with_text - unmapped_source_books,
        "source_reviews_with_unmapped_book_id": unmapped_source_books,
        "duplicate_composite_key_groups": duplicate_source_keys,
        "rows_in_duplicate_composite_key_groups": duplicate_source_rows,
        "book_metadata_count": len(books_by_number),
        "va_books_with_metadata": sum(book_id in books_by_goodreads for book_id in {r['id'] for r in records}),
    }
    if unmatched_indexes or unused_source_rows:
        preview = ", ".join(map(str, unmatched_indexes[:10]))
        raise ValueError(
            f"Metadata join was not one-to-one: {len(unmatched_indexes)} VA rows unmatched "
            f"(indexes: {preview}); {unused_source_rows} source rows unused."
        )
    return enriched, diagnostics, books_by_goodreads


def is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def gini(values: Sequence[float]) -> float:
    array = np.sort(np.asarray(values, dtype=float))
    if array.size == 0 or np.sum(array) == 0:
        return math.nan
    positions = np.arange(1, array.size + 1)
    return float((2 * np.sum(positions * array) / np.sum(array) - (array.size + 1)) / array.size)


def concentration(values: Sequence[float]) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    if array.size == 0 or np.sum(array) == 0:
        return math.nan, math.nan
    shares = array / np.sum(array)
    hhi = float(np.sum(shares**2))
    return hhi, 1.0 / hhi


def parse_review_date(value: str) -> date:
    return datetime.strptime(value, "%B %d, %Y").date()


def percentile(values: Sequence[float], q: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=float), q))


def numeric_summary(name: str, values: Sequence[float]) -> dict[str, Any]:
    array = np.asarray(values, dtype=float)
    finite = array[np.isfinite(array)]
    if finite.size == 0:
        return {"variable": name, "count": 0}
    q1, median, q3 = np.percentile(finite, [25, 50, 75])
    iqr = q3 - q1
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = int(np.sum((finite < low) | (finite > high)))
    return {
        "variable": name,
        "count": int(finite.size),
        "missing_or_nonfinite": int(array.size - finite.size),
        "mean": float(np.mean(finite)),
        "std": float(np.std(finite, ddof=1)) if finite.size > 1 else 0.0,
        "min": float(np.min(finite)),
        "p01": percentile(finite, 1),
        "p25": float(q1),
        "median": float(median),
        "p75": float(q3),
        "p99": percentile(finite, 99),
        "max": float(np.max(finite)),
        "iqr": float(iqr),
        "iqr_outlier_count": outliers,
        "iqr_outlier_percent": 100.0 * outliers / finite.size,
        "zero_count": int(np.sum(finite == 0)),
        "zero_percent": 100.0 * float(np.mean(finite == 0)),
    }


def rank_average_ties(values: Sequence[float]) -> np.ndarray:
    """Return one-based average ranks, matching standard Spearman handling."""
    array = np.asarray(values, dtype=float)
    order = np.argsort(array, kind="mergesort")
    sorted_values = array[order]
    sorted_ranks = np.empty(array.size, dtype=float)
    start = 0
    while start < array.size:
        end = start + 1
        while end < array.size and sorted_values[end] == sorted_values[start]:
            end += 1
        sorted_ranks[start:end] = (start + 1 + end) / 2.0
        start = end
    ranks = np.empty(array.size, dtype=float)
    ranks[order] = sorted_ranks
    return ranks


def correlation(x: Sequence[float], y: Sequence[float], method: str) -> float:
    x_array = np.asarray(x, dtype=float)
    y_array = np.asarray(y, dtype=float)
    keep = np.isfinite(x_array) & np.isfinite(y_array)
    x_array, y_array = x_array[keep], y_array[keep]
    if x_array.size < 2 or np.std(x_array) == 0 or np.std(y_array) == 0:
        return math.nan
    if method == "spearman":
        x_array = rank_average_ties(x_array)
        y_array = rank_average_ties(y_array)
    return float(np.corrcoef(x_array, y_array)[0, 1])


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def fmt(value: float, digits: int = 3) -> str:
    return f"{value:,.{digits}f}"


def mean_or_nan(values: Sequence[float]) -> float:
    return float(np.mean(values)) if len(values) else math.nan


def median_or_nan(values: Sequence[float]) -> float:
    return float(np.median(values)) if len(values) else math.nan


def std_or_nan(values: Sequence[float]) -> float:
    return float(np.std(values, ddof=1)) if len(values) > 1 else math.nan


def rating_group(rating: Any) -> str:
    if rating is None:
        return "unrated"
    if float(rating) in {1.0, 2.0}:
        return "low (1–2 stars)"
    if float(rating) == 3.0:
        return "neutral (3 stars)"
    if float(rating) in {4.0, 5.0}:
        return "high (4–5 stars)"
    return "invalid"


def analyze(
    records: list[dict[str, Any]],
    output_dir: Path,
    input_path: Path,
    review_metadata_path: Path | None,
    book_metadata_path: Path | None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    n_rows = len(records)

    # Schema, missingness, uniqueness, and type consistency.
    schema_rows: list[dict[str, Any]] = []
    all_fields = sorted({key for row in records for key in row})
    for field in all_fields:
        values = [row.get(field) for row in records]
        types = Counter(type(value).__name__ for value in values)
        unique_serialized = {json.dumps(value, sort_keys=True) for value in values}
        schema_rows.append(
            {
                "field": field,
                "present_count": sum(field in row for row in records),
                "missing_count": sum(is_missing(value) for value in values),
                "missing_percent": 100.0 * sum(is_missing(value) for value in values) / n_rows,
                "unique_count": len(unique_serialized),
                "observed_types": "; ".join(f"{key}:{value}" for key, value in sorted(types.items())),
            }
        )
    write_csv(
        output_dir / "data_dictionary_and_quality.csv",
        schema_rows,
        ("field", "present_count", "missing_count", "missing_percent", "unique_count", "observed_types"),
    )

    shelf_counts_per_review = [len(row["shelves"]) for row in records]
    text_char_counts = [len(row["text"]) for row in records]
    numeric_values: dict[str, list[float]] = {
        field: [float(row[field]) for row in records] for field in NUMERIC_FIELDS
    }
    numeric_values["shelf_count"] = [float(value) for value in shelf_counts_per_review]
    numeric_values["text_char_count"] = [float(value) for value in text_char_counts]
    numeric_rows = [numeric_summary(field, values) for field, values in numeric_values.items()]
    numeric_fields = (
        "variable", "count", "missing_or_nonfinite", "mean", "std", "min", "p01", "p25",
        "median", "p75", "p99", "max", "iqr", "iqr_outlier_count", "iqr_outlier_percent",
        "zero_count", "zero_percent",
    )
    write_csv(output_dir / "numeric_summary.csv", numeric_rows, numeric_fields)

    # Book-level summaries.
    by_book: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        by_book[row["id"]].append(row)
    book_rows: list[dict[str, Any]] = []
    for book_id, book_records in by_book.items():
        likes = np.asarray([row["likes"] for row in book_records], dtype=float)
        words = np.asarray([row["word_count"] for row in book_records], dtype=float)
        valence = np.asarray([row["valence"] for row in book_records], dtype=float)
        arousal = np.asarray([row["arousal"] for row in book_records], dtype=float)
        book_rows.append(
            {
                "id": book_id,
                "review_count": len(book_records),
                "total_likes": int(np.sum(likes)),
                "mean_likes": float(np.mean(likes)),
                "median_likes": float(np.median(likes)),
                "total_words": int(np.sum(words)),
                "mean_word_count": float(np.mean(words)),
                "median_word_count": float(np.median(words)),
                "mean_valence": float(np.mean(valence)),
                "std_valence": float(np.std(valence, ddof=1)) if len(valence) > 1 else 0.0,
                "mean_arousal": float(np.mean(arousal)),
                "std_arousal": float(np.std(arousal, ddof=1)) if len(arousal) > 1 else 0.0,
                "reviews_with_shelves": sum(bool(row["shelves"]) for row in book_records),
                "unique_shelves": len({shelf for row in book_records for shelf in row["shelves"]}),
            }
        )
    book_rows.sort(key=lambda row: (-row["review_count"], row["id"]))
    book_fields = (
        "id", "review_count", "total_likes", "mean_likes", "median_likes", "total_words",
        "mean_word_count", "median_word_count", "mean_valence", "std_valence", "mean_arousal",
        "std_arousal", "reviews_with_shelves", "unique_shelves",
    )
    write_csv(output_dir / "book_summary.csv", book_rows, book_fields)

    # Shelf frequencies count each review at most once per shelf.
    shelf_reviews: Counter[str] = Counter()
    shelf_books: dict[str, set[str]] = defaultdict(set)
    duplicate_shelves_within_review = 0
    for row in records:
        shelves = row["shelves"]
        duplicate_shelves_within_review += len(shelves) - len(set(shelves))
        for shelf in set(shelves):
            shelf_reviews[shelf] += 1
            shelf_books[shelf].add(row["id"])
    shelved_count = sum(bool(row['shelves']) for row in records)
    shelf_sizes = [len(row['shelves']) for row in records]
    nonempty_sizes = [size for size in shelf_sizes if size]
    shelf_metrics = {
        'total_reviews': n_rows,
        'reviews_with_shelves': shelved_count,
        'reviews_with_shelves_percent': 100 * shelved_count / n_rows,
        'reviews_without_shelves': n_rows - shelved_count,
        'reviews_without_shelves_percent': 100 * (n_rows - shelved_count) / n_rows,
        'total_stored_shelf_assignments': sum(shelf_sizes),
        'unique_shelf_labels': len(shelf_reviews),
        'mean_shelves_per_review': float(np.mean(shelf_sizes)),
        'mean_shelves_per_shelved_review': mean_or_nan(nonempty_sizes),
        'median_shelves_per_shelved_review': median_or_nan(nonempty_sizes),
        'maximum_stored_shelves_per_review': max(shelf_sizes),
        'books_with_shelved_reviews': sum(any(r['shelves'] for r in group) for group in by_book.values()),
        'books_with_shelved_reviews_percent': 100 * sum(any(r['shelves'] for r in group) for group in by_book.values()) / len(by_book),
        'labels_used_in_one_review': sum(count == 1 for count in shelf_reviews.values()),
        'labels_used_in_one_book': sum(len(ids) == 1 for ids in shelf_books.values()),
        'duplicate_assignments_within_reviews': duplicate_shelves_within_review,
    }
    write_csv(output_dir / 'shelf_coverage_summary.csv',
              ({'metric': key, 'value': value} for key, value in shelf_metrics.items()), ('metric', 'value'))
    write_csv(output_dir / 'shelves_per_review.csv',
              ({'shelf_count': size, 'review_count': shelf_sizes.count(size),
                'percent_all_reviews': 100 * shelf_sizes.count(size) / n_rows}
               for size in range(max(shelf_sizes) + 1)),
              ('shelf_count', 'review_count', 'percent_all_reviews'))
    write_csv(output_dir / 'shelf_coverage_by_book.csv',
              ({'id': row['id'], 'review_count': row['review_count'],
                'reviews_with_shelves': row['reviews_with_shelves'],
                'percent_reviews_with_shelves': 100 * row['reviews_with_shelves'] / row['review_count'],
                'unique_shelves': row['unique_shelves']} for row in book_rows),
              ('id', 'review_count', 'reviews_with_shelves', 'percent_reviews_with_shelves', 'unique_shelves'))
    shelf_rows = [
        {
            "shelf": shelf,
            "review_count": count,
            "review_percent": 100.0 * count / n_rows,
            "percent_shelved_reviews": 100.0 * count / shelved_count if shelved_count else math.nan,
            "book_count": len(shelf_books[shelf]),
            "book_percent": 100.0 * len(shelf_books[shelf]) / len(by_book),
        }
        for shelf, count in shelf_reviews.most_common()
    ]
    write_csv(
        output_dir / "shelf_summary.csv",
        shelf_rows,
        ("shelf", "review_count", "review_percent", "percent_shelved_reviews", "book_count", "book_percent"),
    )

    # Exact-text duplication is reported, but records are not removed.
    text_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        text_groups[row["text"]].append(row)
    duplicated_groups = [group for group in text_groups.values() if len(group) > 1]
    duplicate_rows = []
    for group in duplicated_groups:
        ids = sorted({row["id"] for row in group})
        duplicate_rows.append(
            {
                "occurrences": len(group),
                "book_count": len(ids),
                "book_ids": " | ".join(ids),
                "review_indexes": " | ".join(str(row["index"]) for row in group),
                "text_preview": group[0]["text"].replace("\n", " ")[:200],
            }
        )
    duplicate_rows.sort(key=lambda row: (-row["occurrences"], row["review_indexes"]))
    write_csv(
        output_dir / "duplicate_text_groups.csv",
        duplicate_rows,
        ("occurrences", "book_count", "book_ids", "review_indexes", "text_preview"),
    )

    # Pairwise correlations among original and simple derived numeric fields.
    correlation_rows = []
    correlation_names = list(numeric_values)
    for i, field_a in enumerate(correlation_names):
        for field_b in correlation_names[i + 1 :]:
            for method in ("pearson", "spearman"):
                correlation_rows.append(
                    {
                        "variable_1": field_a,
                        "variable_2": field_b,
                        "method": method,
                        "correlation": correlation(numeric_values[field_a], numeric_values[field_b], method),
                        "n": n_rows,
                    }
                )
    write_csv(
        output_dir / "correlations.csv",
        correlation_rows,
        ("variable_1", "variable_2", "method", "correlation", "n"),
    )

    # Overall audit metrics in a simple key/value table.
    record_signatures = [json.dumps(row, sort_keys=True) for row in records]
    indexes = [row["index"] for row in records]
    expected_index_set = set(range(min(indexes), max(indexes) + 1))
    audit_rows = [
        {"metric": "row_count", "value": n_rows},
        {"metric": "column_count", "value": len(all_fields)},
        {"metric": "book_count", "value": len(by_book)},
        {"metric": "unique_text_count", "value": len(text_groups)},
        {"metric": "exact_duplicate_record_count_beyond_first", "value": n_rows - len(set(record_signatures))},
        {"metric": "duplicate_text_group_count", "value": len(duplicated_groups)},
        {"metric": "duplicate_text_rows_beyond_first", "value": sum(len(group) - 1 for group in duplicated_groups)},
        {"metric": "duplicate_text_groups_spanning_books", "value": sum(len({r['id'] for r in group}) > 1 for group in duplicated_groups)},
        {"metric": "duplicate_index_count_beyond_first", "value": n_rows - len(set(indexes))},
        {"metric": "index_min", "value": min(indexes)},
        {"metric": "index_max", "value": max(indexes)},
        {"metric": "missing_indexes_within_min_max", "value": len(expected_index_set - set(indexes))},
        {"metric": "unexpected_schema_record_count", "value": sum(not set(EXPECTED_FIELDS).issubset(row) for row in records)},
        {"metric": "valence_outside_0_1", "value": sum(not 0 <= row["valence"] <= 1 for row in records)},
        {"metric": "arousal_outside_0_1", "value": sum(not 0 <= row["arousal"] <= 1 for row in records)},
        {"metric": "negative_likes", "value": sum(row["likes"] < 0 for row in records)},
        {"metric": "negative_word_count", "value": sum(row["word_count"] < 0 for row in records)},
        {"metric": "reviews_without_shelves", "value": sum(not row["shelves"] for row in records)},
        {"metric": "duplicate_shelf_assignments_within_reviews", "value": duplicate_shelves_within_review},
        {"metric": "unique_shelf_count", "value": len(shelf_reviews)},
    ]
    write_csv(output_dir / "audit_summary.csv", audit_rows, ("metric", "value"))

    make_figures(numeric_values, book_rows, shelf_rows, output_dir)
    if all({'rating', 'reviewer_url', 'review_date'}.issubset(row) for row in records):
        local_book_path, books_by_goodreads = local_book_metadata()
        enriched = [dict(row, reviewer_id=pseudonymous_reviewer_id(row['reviewer_url'])) for row in records]
        join_diagnostics = {
            'review_metadata_mode': 'embedded_in_input_no_review_join',
            'input_review_count': len(records),
            'va_books_with_metadata': len({r['id'] for r in records} & books_by_goodreads.keys()),
        }
        additional_lines = analyze_additional_dimensions(
            enriched, output_dir, join_diagnostics, books_by_goodreads, input_path, local_book_path,
        )
    elif review_metadata_path is not None and book_metadata_path is not None:
        enriched, join_diagnostics, books_by_goodreads = enrich_records(
            records, review_metadata_path, book_metadata_path
        )
        additional_lines = analyze_additional_dimensions(
            enriched,
            output_dir,
            join_diagnostics,
            books_by_goodreads,
            review_metadata_path,
            book_metadata_path,
        )
    else:
        additional_lines = [
            "## Requested additional dimensions",
            "",
            "Star-rating, reviewer, and review-date analyses were not run because review-level metadata "
            "was not supplied. Re-run with `--review-metadata PATH --book-metadata PATH`.",
            "",
        ]
    write_report(
        records=records,
        input_path=input_path,
        output_dir=output_dir,
        numeric_rows={row["variable"]: row for row in numeric_rows},
        book_rows=book_rows,
        shelf_rows=shelf_rows,
        correlation_rows=correlation_rows,
        duplicate_groups=duplicated_groups,
        text_groups=text_groups,
        additional_lines=additional_lines,
    )


def make_figures(
    numeric_values: dict[str, list[float]],
    book_rows: list[dict[str, Any]],
    shelf_rows: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    panels = (
        ("likes", "Likes", "#4477AA"),
        ("word_count", "Review word count", "#66CCEE"),
        ("valence", "Valence", "#228833"),
        ("arousal", "Arousal", "#CCBB44"),
    )
    for axis, (field, label, color) in zip(axes.flat, panels):
        values = np.asarray(numeric_values[field])
        upper = float(np.percentile(values, 99)) if field in {"likes", "word_count"} else float(np.max(values))
        plotted = values[values <= upper]
        axis.hist(plotted, bins=35, color=color, edgecolor="white", linewidth=0.4)
        axis.set_title(f"{label} (through 99th percentile)" if len(plotted) < len(values) else label)
        axis.set_xlabel(label)
        axis.set_ylabel("Reviews")
    fig.suptitle("Review-level numeric distributions", fontsize=15)
    fig.tight_layout()
    fig.savefig(output_dir / "numeric_distributions.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(8.5, 6.5))
    plot = axis.hexbin(
        numeric_values["valence"], numeric_values["arousal"], gridsize=45,
        mincnt=1, bins="log", cmap="viridis",
    )
    axis.axvline(np.median(numeric_values["valence"]), color="white", linestyle="--", linewidth=1)
    axis.axhline(np.median(numeric_values["arousal"]), color="white", linestyle="--", linewidth=1)
    axis.set(xlabel="Valence", ylabel="Arousal", title="Review valence and arousal density")
    fig.colorbar(plot, ax=axis, label="Review count (log scale)")
    fig.tight_layout()
    fig.savefig(output_dir / "valence_arousal_density.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    review_counts = np.asarray([row["review_count"] for row in book_rows])
    top_books = book_rows[:20][::-1]
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.5))
    axes[0].hist(review_counts, bins=min(30, max(5, len(set(review_counts)))), color="#AA3377", edgecolor="white")
    axes[0].set(xlabel="Reviews per book", ylabel="Books", title="Book review coverage")
    axes[1].barh([row["id"] for row in top_books], [row["review_count"] for row in top_books], color="#AA3377")
    axes[1].set(xlabel="Reviews", title="20 books with most reviews")
    axes[1].tick_params(axis="y", labelsize=7)
    fig.tight_layout()
    fig.savefig(output_dir / "book_coverage.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    if shelf_rows:
        top_shelves = shelf_rows[:20][::-1]
        fig, axis = plt.subplots(figsize=(10, 7))
        axis.barh([row["shelf"] for row in top_shelves], [row["review_count"] for row in top_shelves], color="#EE6677")
        axis.set(xlabel="Reviews assigned to shelf", title="20 most frequent user shelves")
        fig.tight_layout()
        fig.savefig(output_dir / "top_shelves.png", dpi=180, bbox_inches="tight")
        plt.close(fig)

    names = list(numeric_values)
    corr_matrix = np.asarray(
        [[correlation(numeric_values[a], numeric_values[b], "spearman") for b in names] for a in names]
    )
    fig, axis = plt.subplots(figsize=(8, 7))
    image = axis.imshow(corr_matrix, vmin=-1, vmax=1, cmap="RdBu_r")
    axis.set_xticks(range(len(names)), names, rotation=40, ha="right")
    axis.set_yticks(range(len(names)), names)
    for i in range(len(names)):
        for j in range(len(names)):
            axis.text(j, i, f"{corr_matrix[i, j]:.2f}", ha="center", va="center", fontsize=8)
    axis.set_title("Spearman correlations")
    fig.colorbar(image, ax=axis, shrink=0.8)
    fig.tight_layout()
    fig.savefig(output_dir / "spearman_correlations.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def analyze_additional_dimensions(
    records: list[dict[str, Any]],
    output_dir: Path,
    join_diagnostics: dict[str, Any],
    books_by_goodreads: dict[str, dict[str, str]],
    review_metadata_path: Path,
    book_metadata_path: Path,
) -> list[str]:
    """Analyze ratings, reviewers, corpus balance, and temporal coverage."""
    n_rows = len(records)
    valid_rating_values = {1.0, 2.0, 3.0, 4.0, 5.0}
    invalid_rating_count = sum(
        row["rating"] is not None and float(row["rating"]) not in valid_rating_values for row in records
    )
    if invalid_rating_count:
        raise ValueError(f"Found {invalid_rating_count} ratings outside the expected 1–5 scale.")

    invalid_dates = []
    for row in records:
        try:
            row["parsed_review_date"] = parse_review_date(row["review_date"])
        except (TypeError, ValueError):
            row["parsed_review_date"] = None
            invalid_dates.append(row["review_date"])
        row["rating_group"] = rating_group(row["rating"])
        metadata = books_by_goodreads.get(row["id"], {})
        publication_text = str(metadata.get("publication_date", ""))
        publication_match = next(
            (part for part in publication_text.replace("/", " ").replace("-", " ").split() if part.isdigit() and len(part) == 4),
            None,
        )
        row["publication_year"] = int(publication_match) if publication_match else None

    write_csv(
        output_dir / "metadata_join_audit.csv",
        ({"metric": key, "value": value} for key, value in join_diagnostics.items()),
        ("metric", "value"),
    )

    # Star-rating distribution and its relationship to VA/text properties.
    star_rows = []
    for rating in (1, 2, 3, 4, 5, None):
        subset = [row for row in records if row["rating"] == rating]
        label = "missing" if rating is None else str(rating)
        star_rows.append(
            {
                "rating": label,
                "review_count": len(subset),
                "percent_all_reviews": 100.0 * len(subset) / n_rows,
                "percent_rated_reviews": (
                    100.0 * len(subset) / sum(row["rating"] is not None for row in records)
                    if rating is not None else math.nan
                ),
                "book_count": len({row["id"] for row in subset}),
                "reviewer_count": len({row["reviewer_id"] for row in subset}),
                "mean_valence": mean_or_nan([row["valence"] for row in subset]),
                "median_valence": median_or_nan([row["valence"] for row in subset]),
                "mean_arousal": mean_or_nan([row["arousal"] for row in subset]),
                "mean_word_count": mean_or_nan([row["word_count"] for row in subset]),
            }
        )
    write_csv(
        output_dir / "star_rating_distribution.csv",
        star_rows,
        (
            "rating", "review_count", "percent_all_reviews", "percent_rated_reviews", "book_count",
            "reviewer_count", "mean_valence", "median_valence", "mean_arousal", "mean_word_count",
        ),
    )

    rated = [row for row in records if row["rating"] is not None]
    rating_relationship_rows = []
    for outcome in ("valence", "arousal", "word_count", "likes"):
        for method in ("pearson", "spearman"):
            rating_relationship_rows.append(
                {
                    "scope": "review_level_overall",
                    "variable_1": "star_rating",
                    "variable_2": outcome,
                    "method": method,
                    "correlation": correlation(
                        [row["rating"] for row in rated], [row[outcome] for row in rated], method
                    ),
                    "n": len(rated),
                }
            )
    rated_by_book: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rated:
        rated_by_book[row["id"]].append(row)
    centered_ratings = []
    centered_valence = []
    book_mean_ratings = []
    book_mean_valence = []
    for subset in rated_by_book.values():
        mean_rating = float(np.mean([row["rating"] for row in subset]))
        mean_valence = float(np.mean([row["valence"] for row in subset]))
        book_mean_ratings.append(mean_rating)
        book_mean_valence.append(mean_valence)
        centered_ratings.extend(row["rating"] - mean_rating for row in subset)
        centered_valence.extend(row["valence"] - mean_valence for row in subset)
    for method in ("pearson", "spearman"):
        rating_relationship_rows.extend(
            [
                {
                    "scope": "within_book_centered",
                    "variable_1": "star_rating",
                    "variable_2": "valence",
                    "method": method,
                    "correlation": correlation(centered_ratings, centered_valence, method),
                    "n": len(centered_ratings),
                },
                {
                    "scope": "book_level_means",
                    "variable_1": "mean_star_rating",
                    "variable_2": "mean_valence",
                    "method": method,
                    "correlation": correlation(book_mean_ratings, book_mean_valence, method),
                    "n": len(book_mean_ratings),
                },
            ]
        )
    write_csv(
        output_dir / "rating_relationships.csv",
        rating_relationship_rows,
        ("scope", "variable_1", "variable_2", "method", "correlation", "n"),
    )

    # Evaluation variation by book.
    by_book: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        by_book[row["id"]].append(row)
    book_evaluation_rows = []
    for book_id, subset in by_book.items():
        ratings = [float(row["rating"]) for row in subset if row["rating"] is not None]
        dates = [row["parsed_review_date"] for row in subset if row["parsed_review_date"] is not None]
        metadata = books_by_goodreads.get(book_id, {})
        book_evaluation_rows.append(
            {
                "id": book_id,
                "title": metadata.get("title", ""),
                "publication_year": subset[0]["publication_year"],
                "review_count": len(subset),
                "rated_review_count": len(ratings),
                "rating_coverage_percent": 100.0 * len(ratings) / len(subset),
                "mean_rating": mean_or_nan(ratings),
                "std_rating": std_or_nan(ratings),
                "median_rating": median_or_nan(ratings),
                "low_rating_count": sum(row["rating_group"].startswith("low") for row in subset),
                "neutral_rating_count": sum(row["rating_group"].startswith("neutral") for row in subset),
                "high_rating_count": sum(row["rating_group"].startswith("high") for row in subset),
                "unrated_count": sum(row["rating"] is None for row in subset),
                "mean_valence": mean_or_nan([row["valence"] for row in subset]),
                "std_valence": std_or_nan([row["valence"] for row in subset]),
                "mean_arousal": mean_or_nan([row["arousal"] for row in subset]),
                "within_book_rating_valence_pearson": correlation(
                    [row["rating"] for row in subset if row["rating"] is not None],
                    [row["valence"] for row in subset if row["rating"] is not None],
                    "pearson",
                ),
                "earliest_review_date": min(dates).isoformat() if dates else "",
                "latest_review_date": max(dates).isoformat() if dates else "",
            }
        )
    book_evaluation_rows.sort(key=lambda row: (-row["review_count"], row["id"]))
    write_csv(
        output_dir / "book_evaluation_summary.csv",
        book_evaluation_rows,
        (
            "id", "title", "publication_year", "review_count", "rated_review_count",
            "rating_coverage_percent", "mean_rating", "std_rating", "median_rating", "low_rating_count",
            "neutral_rating_count", "high_rating_count", "unrated_count", "mean_valence", "std_valence",
            "mean_arousal", "within_book_rating_valence_pearson", "earliest_review_date",
            "latest_review_date",
        ),
    )

    variation_rows = []
    for outcome in ("rating", "valence", "arousal"):
        groups = []
        for subset in by_book.values():
            values = [float(row[outcome]) for row in subset if row[outcome] is not None]
            if values:
                groups.append(np.asarray(values))
        all_values = np.concatenate(groups)
        grand_mean = float(np.mean(all_values))
        book_means = np.asarray([np.mean(group) for group in groups])
        ss_total = float(np.sum((all_values - grand_mean) ** 2))
        ss_between = float(sum(len(group) * (np.mean(group) - grand_mean) ** 2 for group in groups))
        ss_within = float(sum(np.sum((group - np.mean(group)) ** 2) for group in groups))
        variation_rows.append(
            {
                "outcome": outcome,
                "review_count": len(all_values),
                "book_count": len(groups),
                "grand_mean": grand_mean,
                "book_mean_min": float(np.min(book_means)),
                "book_mean_p25": float(np.percentile(book_means, 25)),
                "book_mean_median": float(np.median(book_means)),
                "book_mean_p75": float(np.percentile(book_means, 75)),
                "book_mean_max": float(np.max(book_means)),
                "between_book_sd_of_means": std_or_nan(book_means),
                "pooled_within_book_sd": math.sqrt(ss_within / (len(all_values) - len(groups))),
                "eta_squared_book": ss_between / ss_total if ss_total else math.nan,
            }
        )
    write_csv(
        output_dir / "evaluation_variation_by_book.csv",
        variation_rows,
        (
            "outcome", "review_count", "book_count", "grand_mean", "book_mean_min", "book_mean_p25",
            "book_mean_median", "book_mean_p75", "book_mean_max", "between_book_sd_of_means",
            "pooled_within_book_sd", "eta_squared_book",
        ),
    )

    # Reviewer distribution and concentration. Only pseudonymous IDs are saved.
    by_reviewer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        by_reviewer[row["reviewer_id"]].append(row)
    reviewer_rows = []
    for reviewer_id, subset in by_reviewer.items():
        ratings = [float(row["rating"]) for row in subset if row["rating"] is not None]
        dates = [row["parsed_review_date"] for row in subset if row["parsed_review_date"] is not None]
        reviewer_rows.append(
            {
                "reviewer_id": reviewer_id,
                "review_count": len(subset),
                "book_count": len({row["id"] for row in subset}),
                "rated_review_count": len(ratings),
                "mean_rating": mean_or_nan(ratings),
                "low_rating_count": sum(row["rating_group"].startswith("low") for row in subset),
                "high_rating_count": sum(row["rating_group"].startswith("high") for row in subset),
                "total_words": sum(row["word_count"] for row in subset),
                "earliest_review_date": min(dates).isoformat() if dates else "",
                "latest_review_date": max(dates).isoformat() if dates else "",
            }
        )
    reviewer_rows.sort(key=lambda row: (-row["review_count"], row["reviewer_id"]))
    write_csv(
        output_dir / "reviewer_summary.csv",
        reviewer_rows,
        (
            "reviewer_id", "review_count", "book_count", "rated_review_count", "mean_rating",
            "low_rating_count", "high_rating_count", "total_words", "earliest_review_date",
            "latest_review_date",
        ),
    )
    write_csv(
        output_dir / "reviewer_index_map.csv",
        (
            {"index": row["index"], "id": row["id"], "reviewer_id": row["reviewer_id"]}
            for row in sorted(records, key=lambda item: item["index"])
        ),
        ("index", "id", "reviewer_id"),
    )
    reviewer_counts = np.asarray([row["review_count"] for row in reviewer_rows], dtype=float)
    reviewer_book_counts = np.asarray([row["book_count"] for row in reviewer_rows], dtype=float)
    sorted_reviewer_counts = np.sort(reviewer_counts)[::-1]
    reviewer_hhi, reviewer_effective_n = concentration(reviewer_counts)

    def top_share(fraction: float) -> float:
        count = max(1, math.ceil(len(sorted_reviewer_counts) * fraction))
        return float(np.sum(sorted_reviewer_counts[:count]) / np.sum(sorted_reviewer_counts))

    reviewer_metric_rows = [
        {"metric": "unique_reviewers", "value": len(reviewer_rows)},
        {"metric": "single_review_reviewers", "value": int(np.sum(reviewer_counts == 1))},
        {"metric": "single_review_reviewer_percent", "value": 100.0 * float(np.mean(reviewer_counts == 1))},
        {"metric": "reviewers_covering_multiple_books", "value": int(np.sum(reviewer_book_counts > 1))},
        {"metric": "multiple_book_reviewer_percent", "value": 100.0 * float(np.mean(reviewer_book_counts > 1))},
        {"metric": "median_reviews_per_reviewer", "value": float(np.median(reviewer_counts))},
        {"metric": "mean_reviews_per_reviewer", "value": float(np.mean(reviewer_counts))},
        {"metric": "maximum_reviews_per_reviewer", "value": int(np.max(reviewer_counts))},
        {"metric": "maximum_books_per_reviewer", "value": int(np.max(reviewer_book_counts))},
        {"metric": "top_1_percent_review_share", "value": top_share(0.01)},
        {"metric": "top_5_percent_review_share", "value": top_share(0.05)},
        {"metric": "top_10_percent_review_share", "value": top_share(0.10)},
        {"metric": "review_count_gini", "value": gini(reviewer_counts)},
        {"metric": "reviewer_hhi", "value": reviewer_hhi},
        {"metric": "effective_reviewer_count", "value": reviewer_effective_n},
    ]
    write_csv(output_dir / "reviewer_concentration.csv", reviewer_metric_rows, ("metric", "value"))

    # High/low corpus diagnostics; neutral and unrated records are retained for context.
    corpus_order = ("low (1–2 stars)", "neutral (3 stars)", "high (4–5 stars)", "unrated")
    corpus_rows = []
    for group_name in corpus_order:
        subset = [row for row in records if row["rating_group"] == group_name]
        book_counts = Counter(row["id"] for row in subset)
        corpus_reviewer_counts = Counter(row["reviewer_id"] for row in subset)
        book_hhi, effective_books = concentration(list(book_counts.values()))
        corpus_reviewer_hhi, effective_reviewers = concentration(list(corpus_reviewer_counts.values()))
        ratings = [float(row["rating"]) for row in subset if row["rating"] is not None]
        corpus_rows.append(
            {
                "corpus": group_name,
                "ratings_included": {"low (1–2 stars)": "1, 2", "neutral (3 stars)": "3", "high (4–5 stars)": "4, 5", "unrated": "missing"}[group_name],
                "review_count": len(subset),
                "review_percent": 100.0 * len(subset) / n_rows,
                "book_count": len(book_counts),
                "book_coverage_percent": 100.0 * len(book_counts) / len(by_book),
                "reviewer_count": len(corpus_reviewer_counts),
                "total_words": sum(row["word_count"] for row in subset),
                "mean_word_count": mean_or_nan([row["word_count"] for row in subset]),
                "median_word_count": median_or_nan([row["word_count"] for row in subset]),
                "mean_likes": mean_or_nan([row["likes"] for row in subset]),
                "reviews_with_shelves_percent": 100.0 * sum(bool(row["shelves"]) for row in subset) / len(subset),
                "mean_rating": mean_or_nan(ratings),
                "mean_valence": mean_or_nan([row["valence"] for row in subset]),
                "mean_arousal": mean_or_nan([row["arousal"] for row in subset]),
                "book_hhi": book_hhi,
                "effective_book_count": effective_books,
                "reviewer_hhi": corpus_reviewer_hhi,
                "effective_reviewer_count": effective_reviewers,
            }
        )
    write_csv(
        output_dir / "evaluation_corpus_diagnostics.csv",
        corpus_rows,
        (
            "corpus", "ratings_included", "review_count", "review_percent", "book_count",
            "book_coverage_percent", "reviewer_count", "total_words", "mean_word_count",
            "median_word_count", "mean_likes", "reviews_with_shelves_percent", "mean_rating",
            "mean_valence", "mean_arousal", "book_hhi", "effective_book_count", "reviewer_hhi",
            "effective_reviewer_count",
        ),
    )
    corpus_book_rows = []
    for book_id, subset in by_book.items():
        counts = Counter(row["rating_group"] for row in subset)
        metadata = books_by_goodreads.get(book_id, {})
        rated_count = sum(row["rating"] is not None for row in subset)
        corpus_book_rows.append(
            {
                "id": book_id,
                "title": metadata.get("title", ""),
                "total_reviews": len(subset),
                "low_reviews": counts["low (1–2 stars)"],
                "neutral_reviews": counts["neutral (3 stars)"],
                "high_reviews": counts["high (4–5 stars)"],
                "unrated_reviews": counts["unrated"],
                "low_percent_rated": 100.0 * counts["low (1–2 stars)"] / rated_count if rated_count else math.nan,
                "high_percent_rated": 100.0 * counts["high (4–5 stars)"] / rated_count if rated_count else math.nan,
            }
        )
    corpus_book_rows.sort(key=lambda row: (-row["total_reviews"], row["id"]))
    write_csv(
        output_dir / "evaluation_corpus_by_book.csv",
        corpus_book_rows,
        (
            "id", "title", "total_reviews", "low_reviews", "neutral_reviews", "high_reviews",
            "unrated_reviews", "low_percent_rated", "high_percent_rated",
        ),
    )

    # Review dates plus publication-year coverage.
    dated = [row for row in records if row["parsed_review_date"] is not None]
    years = range(min(row["parsed_review_date"].year for row in dated), max(row["parsed_review_date"].year for row in dated) + 1)
    review_year_rows = []
    for year in years:
        subset = [row for row in dated if row["parsed_review_date"].year == year]
        ratings = [float(row["rating"]) for row in subset if row["rating"] is not None]
        counts = Counter(row["rating_group"] for row in subset)
        review_year_rows.append(
            {
                "review_year": year,
                "review_count": len(subset),
                "book_count": len({row["id"] for row in subset}),
                "reviewer_count": len({row["reviewer_id"] for row in subset}),
                "low_review_count": counts["low (1–2 stars)"],
                "neutral_review_count": counts["neutral (3 stars)"],
                "high_review_count": counts["high (4–5 stars)"],
                "unrated_review_count": counts["unrated"],
                "mean_rating": mean_or_nan(ratings),
                "mean_valence": mean_or_nan([row["valence"] for row in subset]),
                "mean_arousal": mean_or_nan([row["arousal"] for row in subset]),
            }
        )
    write_csv(
        output_dir / "review_year_summary.csv",
        review_year_rows,
        (
            "review_year", "review_count", "book_count", "reviewer_count", "low_review_count",
            "neutral_review_count", "high_review_count", "unrated_review_count", "mean_rating",
            "mean_valence", "mean_arousal",
        ),
    )

    publication_counts = Counter(
        row["publication_year"] for row in records if row["publication_year"] is not None
    )
    publication_book_counts = Counter(
        row["publication_year"] for row in {book_id: subset[0] for book_id, subset in by_book.items()}.values()
        if row["publication_year"] is not None
    )
    publication_rows = [
        {
            "publication_year": year,
            "book_count": publication_book_counts[year],
            "review_count": publication_counts[year],
        }
        for year in sorted(publication_book_counts)
    ]
    write_csv(
        output_dir / "book_publication_year_summary.csv",
        publication_rows,
        ("publication_year", "book_count", "review_count"),
    )
    review_ages = [
        row["parsed_review_date"].year - row["publication_year"]
        for row in dated if row["publication_year"] is not None
    ]
    temporal_metric_rows = [
        {"metric": "dated_review_count", "value": len(dated)},
        {"metric": "invalid_or_missing_review_date_count", "value": n_rows - len(dated)},
        {"metric": "earliest_review_date", "value": min(row["parsed_review_date"] for row in dated).isoformat()},
        {"metric": "latest_review_date", "value": max(row["parsed_review_date"] for row in dated).isoformat()},
        {"metric": "review_year_count", "value": len({row["parsed_review_date"].year for row in dated})},
        {"metric": "books_with_publication_year", "value": sum(publication_book_counts.values())},
        {"metric": "distinct_publication_year_count", "value": len(publication_book_counts)},
        {"metric": "earliest_book_publication_year", "value": min(publication_book_counts)},
        {"metric": "latest_book_publication_year", "value": max(publication_book_counts)},
        {"metric": "median_review_age_years", "value": float(np.median(review_ages))},
        {"metric": "reviews_predating_publication_year", "value": sum(age < 0 for age in review_ages)},
    ]
    write_csv(output_dir / "temporal_coverage_audit.csv", temporal_metric_rows, ("metric", "value"))

    make_additional_figures(
        records, star_rows, book_evaluation_rows, reviewer_counts, corpus_rows,
        review_year_rows, publication_rows, output_dir,
    )

    star_counts = {row["rating"]: row["review_count"] for row in star_rows}
    spearman_rating_valence = next(
        row["correlation"] for row in rating_relationship_rows
        if row["scope"] == "review_level_overall" and row["variable_2"] == "valence"
        and row["method"] == "spearman"
    )
    pearson_rating_valence = next(
        row["correlation"] for row in rating_relationship_rows
        if row["scope"] == "review_level_overall" and row["variable_2"] == "valence"
        and row["method"] == "pearson"
    )
    within_book_rating_valence = next(
        row["correlation"] for row in rating_relationship_rows
        if row["scope"] == "within_book_centered" and row["method"] == "pearson"
    )
    book_mean_rating_valence = next(
        row["correlation"] for row in rating_relationship_rows
        if row["scope"] == "book_level_means" and row["method"] == "pearson"
    )
    high_row = next(row for row in corpus_rows if row["corpus"].startswith("high"))
    low_row = next(row for row in corpus_rows if row["corpus"].startswith("low"))
    valid_ratings = [row["rating"] for row in records if row["rating"] is not None]
    rating_variation = next(row for row in variation_rows if row["outcome"] == "rating")
    valence_variation = next(row for row in variation_rows if row["outcome"] == "valence")
    earliest_date = min(row["parsed_review_date"] for row in dated)
    latest_date = max(row["parsed_review_date"] for row in dated)

    lines = [
        "## Requested additional dimensions",
        "",
        f"Review metadata source: `{review_metadata_path}`  ",
        f"Book metadata source: `{book_metadata_path}`",
        "",
        (f"All {n_rows:,} reviews use ratings, reviewer URLs, and dates already present in the input JSON; no review-metadata join was performed. "
         if join_diagnostics.get('review_metadata_mode') == 'embedded_in_input_no_review_join'
         else f"The enrichment matched all {n_rows:,} VA records using Goodreads book ID, exact text, likes, shelves, and word count. ")
        + "Reviewer profile URLs were converted to deterministic pseudonymous IDs for the reviewer outputs. Book publication metadata was matched by Goodreads ID.",
        "",
        "### Star-rating distribution and textual valence",
        "",
        f"Ratings are present for {len(valid_ratings):,} reviews ({100*len(valid_ratings)/n_rows:.1f}%); {star_counts['missing']:,} ({100*star_counts['missing']/n_rows:.1f}%) are unrated. The mean is {np.mean(valid_ratings):.3f} and the median is {np.median(valid_ratings):.0f} stars.",
        "",
        "| Stars | Reviews | % of rated | Mean valence |",
        "|---:|---:|---:|---:|",
    ]
    for row in star_rows[:5]:
        lines.append(f"| {row['rating']} | {row['review_count']:,} | {row['percent_rated_reviews']:.1f}% | {row['mean_valence']:.3f} |")
    lines += [
        "",
        f"Star rating and textual valence agree positively but only moderately (Pearson *r* = {pearson_rating_valence:.3f}; Spearman ρ = {spearman_rating_valence:.3f}; *n* = {len(rated):,}). The association remains similar after centering both measures within books (*r* = {within_book_rating_valence:.3f}); book-level means correlate more strongly (*r* = {book_mean_rating_valence:.3f}, {len(book_mean_ratings)} books). The measures are therefore related but non-interchangeable.",
        "",
        "### Evaluation variation by book",
        "",
        f"Mean star ratings across books range from {rating_variation['book_mean_min']:.2f} to {rating_variation['book_mean_max']:.2f}; the middle 50% range is {rating_variation['book_mean_p25']:.2f}–{rating_variation['book_mean_p75']:.2f}. Book ID accounts descriptively for {100*rating_variation['eta_squared_book']:.1f}% of review-level rating variance and {100*valence_variation['eta_squared_book']:.1f}% of valence variance (unadjusted η²). This establishes material individual-book heterogeneity but is not an inferential multilevel estimate.",
        "",
        "### Reviewer distribution and concentration",
        "",
        f"The corpus contains {len(reviewer_rows):,} pseudonymous reviewers. {int(np.sum(reviewer_counts == 1)):,} ({100*np.mean(reviewer_counts == 1):.1f}%) contribute one review; {int(np.sum(reviewer_book_counts > 1)):,} ({100*np.mean(reviewer_book_counts > 1):.1f}%) cover multiple books. The most active reviewer contributes {int(np.max(reviewer_counts))} reviews. The top 1% of reviewers contribute {100*top_share(0.01):.1f}% of reviews (Gini = {gini(reviewer_counts):.3f}; effective reviewer count = {reviewer_effective_n:,.0f}).",
        "",
        "### High-/low-evaluation corpus diagnostics",
        "",
        "High evaluation is defined as 4–5 stars and low evaluation as 1–2 stars; 3-star and unrated reviews are excluded from a binary high/low comparison but retained in the diagnostics.",
        "",
        "| Corpus | Reviews | Books | Reviewers | Total words | Mean words | Mean valence |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| Low | {low_row['review_count']:,} | {low_row['book_count']:,} | {low_row['reviewer_count']:,} | {low_row['total_words']:,} | {low_row['mean_word_count']:.1f} | {low_row['mean_valence']:.3f} |",
        f"| High | {high_row['review_count']:,} | {high_row['book_count']:,} | {high_row['reviewer_count']:,} | {high_row['total_words']:,} | {high_row['mean_word_count']:.1f} | {high_row['mean_valence']:.3f} |",
        "",
        f"The high corpus has {high_row['review_count']/low_row['review_count']:.2f}× as many reviews and {high_row['total_words']/low_row['total_words']:.2f}× as many words as the low corpus. Both are dispersed across many books ({low_row['book_count']} low; {high_row['book_count']} high), but raw keyword counts will be dominated by the larger high corpus. Later keyness work should use normalized rates/effect sizes and a balanced-resampling sensitivity check.",
        "",
        "### Temporal coverage",
        "",
        f"All review dates parsed successfully and span {earliest_date.isoformat()} to {latest_date.isoformat()}. All {sum(publication_book_counts.values())} reviewed books have a listed publication year, spanning {min(publication_book_counts)}–{max(publication_book_counts)}. However, {sum(age < 0 for age in review_ages):,} reviews predate the listed publication year, probably because the metadata describes a later edition; review-age calculations should therefore not be used without edition-level reconciliation. Because the latest review is from {latest_date.year}, claims about “present” readerly expectations should be qualified as applying to Goodreads reviews collected through {latest_date.isoformat()}, not to an unbounded present.",
        "",
        "Additional outputs: `star_rating_distribution.csv`, `rating_relationships.csv`, `book_evaluation_summary.csv`, `evaluation_variation_by_book.csv`, `reviewer_summary.csv`, `reviewer_index_map.csv`, `reviewer_concentration.csv`, `evaluation_corpus_diagnostics.csv`, `evaluation_corpus_by_book.csv`, `review_year_summary.csv`, `book_publication_year_summary.csv`, `temporal_coverage_audit.csv`, `metadata_join_audit.csv`, and five additional PNG figures.",
        "",
    ]
    return lines


def make_additional_figures(
    records: list[dict[str, Any]],
    star_rows: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    reviewer_counts: np.ndarray,
    corpus_rows: list[dict[str, Any]],
    review_year_rows: list[dict[str, Any]],
    publication_rows: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    rated = [row for row in records if row["rating"] is not None]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    rating_labels = [str(row["rating"]) for row in star_rows[:5]]
    rating_counts = [row["review_count"] for row in star_rows[:5]]
    axes[0].bar(rating_labels, rating_counts, color="#4477AA")
    axes[0].set(xlabel="Star rating", ylabel="Reviews", title="Star-rating distribution")
    for x, value in enumerate(rating_counts):
        axes[0].text(x, value, f"{value:,}", ha="center", va="bottom", fontsize=8)
    valence_by_rating = [
        [row["valence"] for row in rated if row["rating"] == rating] for rating in range(1, 6)
    ]
    axes[1].boxplot(valence_by_rating, labels=range(1, 6), showfliers=False)
    axes[1].set(xlabel="Star rating", ylabel="Textual valence", title="Valence by star rating")
    fig.tight_layout()
    fig.savefig(output_dir / "star_rating_and_valence.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    plottable_books = [row for row in book_rows if not math.isnan(row["mean_rating"])]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    scatter = axes[0].scatter(
        [row["mean_rating"] for row in plottable_books],
        [row["mean_valence"] for row in plottable_books],
        s=[15 + math.sqrt(row["rated_review_count"]) * 4 for row in plottable_books],
        c=[row["rated_review_count"] for row in plottable_books], cmap="viridis", alpha=0.75,
    )
    axes[0].set(xlabel="Book mean star rating", ylabel="Book mean valence", title="Mean evaluation by book")
    fig.colorbar(scatter, ax=axes[0], label="Rated reviews")
    axes[1].hist([row["mean_rating"] for row in plottable_books], bins=20, color="#228833", alpha=0.8)
    axes[1].set(xlabel="Book mean star rating", ylabel="Books", title="Distribution of book means")
    fig.tight_layout()
    fig.savefig(output_dir / "book_evaluation_variation.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    max_reviews = int(np.max(reviewer_counts))
    axes[0].hist(reviewer_counts, bins=np.arange(0.5, max_reviews + 1.5), color="#AA3377")
    axes[0].set_yscale("log")
    axes[0].set(xlabel="Reviews per reviewer", ylabel="Reviewers (log scale)", title="Reviewer contribution distribution")
    ascending = np.sort(reviewer_counts)
    lorenz = np.insert(np.cumsum(ascending) / np.sum(ascending), 0, 0)
    population = np.linspace(0, 1, len(lorenz))
    axes[1].plot(population, lorenz, color="#AA3377", linewidth=2)
    axes[1].plot([0, 1], [0, 1], linestyle="--", color="gray")
    axes[1].set(xlabel="Cumulative share of reviewers", ylabel="Cumulative share of reviews", title="Reviewer concentration (Lorenz curve)")
    fig.tight_layout()
    fig.savefig(output_dir / "reviewer_distribution.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    high_low = [row for row in corpus_rows if row["corpus"].startswith(("low", "high"))]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    labels = ["Low\n(1–2)", "High\n(4–5)"]
    axes[0].bar(labels, [row["review_count"] for row in high_low], color=["#4477AA", "#EE6677"])
    axes[0].set(ylabel="Reviews", title="High/low corpus size")
    axes[1].bar(labels, [row["total_words"] for row in high_low], color=["#4477AA", "#EE6677"])
    axes[1].set(ylabel="Total words", title="High/low textual volume")
    fig.tight_layout()
    fig.savefig(output_dir / "evaluation_corpus_balance.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=False)
    years = [row["review_year"] for row in review_year_rows]
    bottoms = np.zeros(len(years))
    temporal_layers = (
        ("low_review_count", "Low (1–2)", "#4477AA"),
        ("neutral_review_count", "Neutral (3)", "#CCBB44"),
        ("high_review_count", "High (4–5)", "#EE6677"),
        ("unrated_review_count", "Unrated", "#BBBBBB"),
    )
    for field, label, color in temporal_layers:
        values = np.asarray([row[field] for row in review_year_rows])
        axes[0].bar(years, values, bottom=bottoms, label=label, color=color)
        bottoms += values
    axes[0].set(ylabel="Reviews", title="Review coverage by year")
    axes[0].legend(ncols=4, fontsize=8)
    axes[0].set_xticks(years, [str(year) for year in years], rotation=45, ha="right")
    publication_years = [row["publication_year"] for row in publication_rows]
    axes[1].bar(publication_years, [row["book_count"] for row in publication_rows], color="#228833")
    axes[1].set(xlabel="Publication year", ylabel="Books", title="Publication-year coverage of reviewed books")
    axes[1].set_xticks(publication_years, [str(year) for year in publication_years], rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(output_dir / "temporal_coverage.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def write_report(
    records: list[dict[str, Any]],
    input_path: Path,
    output_dir: Path,
    numeric_rows: dict[str, dict[str, Any]],
    book_rows: list[dict[str, Any]],
    shelf_rows: list[dict[str, Any]],
    correlation_rows: list[dict[str, Any]],
    duplicate_groups: list[list[dict[str, Any]]],
    text_groups: dict[str, list[dict[str, Any]]],
    additional_lines: list[str],
) -> None:
    n = len(records)
    word = numeric_rows["word_count"]
    likes = numeric_rows["likes"]
    valence = numeric_rows["valence"]
    arousal = numeric_rows["arousal"]
    book_counts = np.asarray([row["review_count"] for row in book_rows])
    shelf_empty = sum(not row["shelves"] for row in records)
    duplicate_extra = sum(len(group) - 1 for group in duplicate_groups)
    cross_book_groups = sum(len({row["id"] for row in group}) > 1 for group in duplicate_groups)
    strongest = sorted(
        (row for row in correlation_rows if row["method"] == "spearman"),
        key=lambda row: abs(row["correlation"]), reverse=True,
    )[:5]

    lines = [
        "# Descriptive analysis: AllReviews_217_VA",
        "",
        f"Source: `{input_path}`  ",
        f"Unit of analysis: one review record. Dataset-internal text was treated only as data.",
        "",
        "## Dataset and data quality",
        "",
        f"- {n:,} reviews across {len(book_rows):,} unique book IDs ({len(records[0]):,} fields per record).",
        "- Missing values by stored field: " + "; ".join(f"{field}: {sum(is_missing(row.get(field)) for row in records):,}" for field in records[0]) + ".",
        f"- Index values are unique and span {min(row['index'] for row in records):,}–{max(row['index'] for row in records):,}; they retain {len(set(range(min(row['index'] for row in records), max(row['index'] for row in records) + 1)) - {row['index'] for row in records}):,} gaps from the source indexing.",
        f"- There are no exact duplicate full records. Exact text is repeated in {len(duplicate_groups):,} groups, representing {duplicate_extra:,} additional rows beyond the first; {cross_book_groups:,} groups span more than one book.",
        f"- {shelf_empty:,} reviews ({100*shelf_empty/n:.1f}%) have no shelf labels. This is absence of optional shelf metadata, not a missing JSON field.",
        f"- All valence/arousal values fall in [0, 1], and likes/word counts are nonnegative.",
        "",
        "## Review-level distributions",
        "",
        "| Variable | Mean | SD | Median | P25–P75 | Min–Max | Zero % |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| Likes | {fmt(likes['mean'])} | {fmt(likes['std'])} | {fmt(likes['median'])} | {fmt(likes['p25'])}–{fmt(likes['p75'])} | {fmt(likes['min'])}–{fmt(likes['max'])} | {fmt(likes['zero_percent'], 1)}% |",
        f"| Word count | {fmt(word['mean'])} | {fmt(word['std'])} | {fmt(word['median'])} | {fmt(word['p25'])}–{fmt(word['p75'])} | {fmt(word['min'])}–{fmt(word['max'])} | {fmt(word['zero_percent'], 1)}% |",
        f"| Valence | {fmt(valence['mean'])} | {fmt(valence['std'])} | {fmt(valence['median'])} | {fmt(valence['p25'])}–{fmt(valence['p75'])} | {fmt(valence['min'])}–{fmt(valence['max'])} | {fmt(valence['zero_percent'], 1)}% |",
        f"| Arousal | {fmt(arousal['mean'])} | {fmt(arousal['std'])} | {fmt(arousal['median'])} | {fmt(arousal['p25'])}–{fmt(arousal['p75'])} | {fmt(arousal['min'])}–{fmt(arousal['max'])} | {fmt(arousal['zero_percent'], 1)}% |",
        "",
        f"Likes are strongly right-skewed: {fmt(likes['zero_percent'], 1)}% of reviews have zero likes, while the maximum is {likes['max']:,.0f}. Word counts are also right-skewed (median {word['median']:,.0f}, mean {word['mean']:,.1f}, maximum {word['max']:,.0f}), so medians/IQRs should accompany means/SDs in later analysis.",
        "",
        "## Coverage by book and shelf",
        "",
        f"Books contain a median of {np.median(book_counts):,.0f} reviews (range {np.min(book_counts):,.0f}–{np.max(book_counts):,.0f}; mean {np.mean(book_counts):,.1f}).",
        "",
        "Most-reviewed books:",
        "",
        "| Book ID | Reviews | Mean valence | Mean arousal |",
        "|---|---:|---:|---:|",
    ]
    for row in book_rows[:10]:
        lines.append(f"| {row['id']} | {row['review_count']:,} | {row['mean_valence']:.3f} | {row['mean_arousal']:.3f} |")
    sizes = Counter(len(row['shelves']) for row in records)
    shelved = n - shelf_empty
    assignments = sum(size * count for size, count in sizes.items())
    lines += ["", "### Shelf coverage", "",
              f"Shelf labels are present on {shelved:,} reviews ({100*shelved/n:.1f}%); {shelf_empty:,} ({100*shelf_empty/n:.1f}%) have empty shelf lists. There are {assignments:,} stored assignments and {len(shelf_rows):,} distinct labels. Among reviews with shelves, the mean number of labels is {assignments/shelved:.2f}. Labels occur across {sum(row['reviews_with_shelves'] > 0 for row in book_rows)} of {len(book_rows)} books.",
              "", "| Stored labels per review | Reviews | % of all reviews |", "|---:|---:|---:|"]
    for size, count in sorted(sizes.items()):
        lines.append(f"| {size} | {count:,} | {100*count/n:.1f}% |")
    lines += ["", "Counts describe stored shelf metadata. An empty list does not establish that a reviewer never shelved the book. The observed maximum is not evidence of a platform limit. Labels are retained verbatim (for example, graphic-novel and graphic-novels remain separate); labels overlap, so percentages across labels are not additive.",
              "", "Additional tables: `shelf_coverage_summary.csv` (coverage, assignments, and rare labels), `shelves_per_review.csv` (label-count distribution), and `shelf_coverage_by_book.csv` (coverage within each book). In `shelf_summary.csv`, `review_percent` uses all reviews as the denominator and `percent_shelved_reviews` uses only reviews with at least one stored label.",
              "", "Most frequent shelves:", "",
              f"Review range is the number of distinct review records containing a label, expressed as a percentage of all {n:,} reviews. Book range is the number of distinct books with at least one such review, expressed as a percentage of all {len(book_rows):,} books. Each label is counted at most once per review and once per book; these ranges measure dispersion, not minimum–maximum intervals.",
              "", "| Shelf | Reviews | Review range (%) | Books | Book range (%) |", "|---|---:|---:|---:|---:|"]
    for row in shelf_rows[:10]:
        lines.append(f"| {row['shelf']} | {row['review_count']:,} | {row['review_percent']:.2f}% | {row['book_count']:,} | {row['book_percent']:.2f}% |")

    lines += [
        "",
        "## Numeric associations",
        "",
        "The five largest absolute review-level Spearman correlations are shown below. These are descriptive associations only; reviews are clustered within books and no causal interpretation is warranted.",
        "",
        "| Variable 1 | Variable 2 | Spearman ρ |",
        "|---|---|---:|",
    ]
    for row in strongest:
        lines.append(f"| {row['variable_1']} | {row['variable_2']} | {row['correlation']:.3f} |")

    lines += [
        "",
        "## Files produced",
        "",
        "- `audit_summary.csv`: dataset-wide validation counts.",
        "- `data_dictionary_and_quality.csv`: type, completeness, and uniqueness by field.",
        "- `numeric_summary.csv`: central tendency, dispersion, percentiles, zero counts, and IQR outliers.",
        "- `book_summary.csv`: review volume, engagement, length, VA, and shelf coverage for every book.",
        "- `shelf_summary.csv`: review- and book-level shelf frequencies.",
        "- `duplicate_text_groups.csv`: exact repeated-text groups for review, not automatic deletion.",
        "- `correlations.csv`: pairwise Pearson and Spearman correlations.",
        "- PNG figures: numeric distributions, VA density, book coverage, top shelves, and Spearman correlations.",
        "",
        "## Interpretation notes",
        "",
        "- The `id` field is treated as a book identifier and the review is the observational unit.",
        "- Shelf labels are user-generated and multi-valued; frequencies overlap and should not be summed as mutually exclusive categories.",
        "- IQR outliers are flags for unusual values, not evidence of invalidity; no observations were removed.",
        "- For book comparisons, review-count imbalance and within-book clustering should be handled explicitly in inferential models.",
        "",
    ]
    lines += additional_lines
    (output_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_path = args.input.expanduser().resolve()
    output_dir = args.output.expanduser().resolve()
    review_metadata_path = args.review_metadata.expanduser().resolve() if args.review_metadata else None
    book_metadata_path = args.book_metadata.expanduser().resolve() if args.book_metadata else None
    records = load_records(input_path)
    analyze(records, output_dir, input_path, review_metadata_path, book_metadata_path)
    print(f"Analyzed {len(records):,} reviews.")
    print(f"Results written to {output_dir}")


if __name__ == "__main__":
    main()
