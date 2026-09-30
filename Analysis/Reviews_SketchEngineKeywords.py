"""Export complete rating-subcorpus comparisons from Sketch Engine.

Requires requests. API.md contains only the API key; it is never copied to outputs.
Run from the repository root. Existing matching API responses can be resumed.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import time

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://api.sketchengine.eu"
N_VALUES = (1, 10, 100, 1000)
COLUMNS = {
    "item": "item",
    "score": "keyness_score",
    "frq1": "focus_count",
    "frq2": "reference_count",
    "rel_frq1": "focus_relative_frequency_per_million_tokens",
    "rel_frq2": "reference_relative_frequency_per_million_tokens",
    "docf1": "focus_docf",
    "docf2": "reference_docf",
    "rel_docf1": "focus_relative_docf_percent",
    "rel_docf2": "reference_relative_docf_percent",
    "arf1": "focus_arf",
    "arf2": "reference_arf",
    "aldf1": "focus_aldf",
    "aldf2": "reference_aldf",
    "query": "cql_query",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class Client:
    def __init__(self, key_file):
        self.key = key_file.read_text(encoding="utf-8").strip()
        if not self.key or any(c.isspace() for c in self.key):
            raise ValueError("The key file must contain only the API key.")
        self.session = requests.Session()
        self.session.headers["Authorization"] = "Bearer " + self.key
        self.last_call = 0.0

    def get(self, endpoint, params):
        deadline = time.monotonic() + 1800
        while time.monotonic() < deadline:
            time.sleep(max(0, 1.2 - (time.monotonic() - self.last_call)))
            self.last_call = time.monotonic()
            response = self.session.get(BASE_URL + endpoint, params=params,
                                        timeout=180, allow_redirects=False)
            if response.status_code == 429:
                print("Rate limit: waiting 30 seconds.", flush=True)
                time.sleep(30)
                continue
            if response.status_code != 200:
                raise RuntimeError(f"Sketch Engine returned HTTP {response.status_code} for {endpoint}")
            if self.key in response.text:
                raise RuntimeError("Refusing to save a response containing the credential.")
            payload = response.json()
            if payload.get("error"):
                raise RuntimeError(str(payload["error"]).replace(self.key, "[REDACTED]"))
            if payload.get("jobid"):
                print("Computing:", payload.get("desc", "background statistics"), flush=True)
                time.sleep(5)
                continue
            return payload
        raise TimeoutError("Sketch Engine background processing exceeded 30 minutes.")


def validate(payload, params, token_counts):
    rows = payload["keywords"]
    if len(rows) != int(payload["total"]):
        raise ValueError(f"Incomplete response: {len(rows)} of {payload['total']} rows")
    for key, value in params.items():
        if str(payload["request"].get(key)) != str(value):
            raise ValueError(f"Request mismatch for {key}")
    focus_tokens = token_counts[params["usesubcorp"]]
    reference_tokens = token_counts[params["ref_usesubcorp"]]
    if payload["subcorpus_size"] != focus_tokens or payload["reference_subcorpus_size"] != reference_tokens:
        raise ValueError("Subcorpus frequency denominators do not match corpus metadata")
    previous_score = math.inf
    seen = set()
    for row in rows:
        if not COLUMNS.keys() <= row.keys():
            raise ValueError("A required output metric is missing")
        if row["item"] in seen:
            raise ValueError("Duplicate item in extraction")
        seen.add(row["item"])
        if not all(math.isfinite(row[k]) and row[k] >= 0 for k in COLUMNS if k not in ("item", "query")):
            raise ValueError("Non-finite or negative metric")
        if row["score"] > previous_score:
            raise ValueError("Results are not in descending keyness order")
        previous_score = row["score"]
        for side, tokens in ((1, focus_tokens), (2, reference_tokens)):
            count = row[f"frq{side}"]
            rel = row[f"rel_frq{side}"]
            # API rates show single-precision rounding plus five decimal places.
            if not math.isclose(rel, count * 1_000_000 / tokens, rel_tol=1.5e-7, abs_tol=0.000006):
                raise ValueError("Relative frequency does not use the expected token denominator")
            if not 0 <= row[f"docf{side}"] <= count or not 0 <= row[f"rel_docf{side}"] <= 100:
                raise ValueError("Invalid document frequency")
        n = params["simple_n"]
        score = (row["frq1"] * 1_000_000 / focus_tokens + n) / (row["frq2"] * 1_000_000 / reference_tokens + n)
        if not math.isclose(row["score"], score, abs_tol=0.000501, rel_tol=0):
            raise ValueError("Keyness score does not match Simple Maths with the requested N")
    return rows


def write_csv(path, rows):
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["line_number", *COLUMNS.values()])
        for rank, row in enumerate(rows, 1):
            values = [int(row[key]) if key in ("docf1", "docf2") else row[key] for key in COLUMNS]
            writer.writerow([rank, *values])
    temporary.replace(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-key-file", type=Path, default=ROOT / "API.md")
    parser.add_argument("--corpus", default="user/emily.murphy/gb_allreviews")
    parser.add_argument("--high", default="GB_HighRating")
    parser.add_argument("--low", default="GB_LowRating")
    parser.add_argument("--output", type=Path, default=ROOT / "Results/Keywords_Rating")
    parser.add_argument("--resume", action="store_true", help="Reuse matching saved API responses")
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    if not args.resume and (list(output.glob("*_N=*.csv")) or (output / "extraction_settings.json").exists()):
        parser.error("Results exist; choose a new output directory or explicitly use --resume.")
    raw_dir = output / "api_responses"
    raw_dir.mkdir(exist_ok=True)
    client = Client(args.api_key_file)
    metadata = client.get("/search/corp_info", {"corpname": args.corpus, "subcorpora": 1, "format": "json"})
    subcorpora = {s["n"]: s for s in metadata["subcorpora"]}
    for name in (args.high, args.low):
        if name not in subcorpora:
            raise ValueError(f"Subcorpus not found: {name}")
    token_counts = {name: int(subcorpora[name]["tokens"]) for name in (args.high, args.low)}
    if not metadata.get("terms_compiled"):
        raise ValueError("The corpus term grammar has not been compiled")
    manifest_path = output / "extraction_settings.json"
    if args.resume and manifest_path.exists():
        old = json.loads(manifest_path.read_text())
        for key in ("sizes", "subcorpora", "termdef"):
            if old["corpus_metadata"].get(key) != metadata.get(key):
                raise ValueError(f"Corpus metadata changed ({key}); use a new output directory")
    manifest = {
        "started_at_utc": utc_now(), "status": "running", "api_base_url": BASE_URL,
        "corpus": args.corpus, "high_subcorpus": args.high, "low_subcorpus": args.low,
        "corpus_metadata": metadata, "N_values": list(N_VALUES),
        "settings_basis": "Website defaults explicitly confirmed by the user; previous browser query settings were unavailable.",
        "scope": "All returned candidates, including scores at or below 1; no additional stoplist, score threshold, sampling, or manual filtering.",
        "units": {"relative_frequency": "per million subcorpus tokens", "relative_docf": "percent of subcorpus documents"},
        "columns": {"line_number": "One-based rank in Sketch Engine response order", **{v: k for k, v in COLUMNS.items()}},
        "documentation": ["https://www.sketchengine.eu/apidoc/", "https://www.sketchengine.eu/guide/keywords-and-term-extraction/"],
        "runs": [],
    }
    write_json(manifest_path, manifest)
    baseline = {}
    for label, focus, reference in (("High", args.high, args.low), ("Low", args.low, args.high)):
        for kind, attr, flag in (("keywords", "lemma", "keywords"), ("keyterms", "TERM", "terms")):
            for n in N_VALUES:
                stem = f"{label}_{kind}_N={n}"
                params = {"corpname": args.corpus, "usesubcorp": focus,
                          "ref_corpname": args.corpus, "ref_usesubcorp": reference,
                          "simple_n": n, "max_keywords": 1_000_000, "attr": attr, flag: 1,
                          "minfreq": 1, "maxfreq": 0, "alnum": 1, "onealpha": 1,
                          "include_nonwords": 0, "icase": 1, "wlpat": ".*",
                          "addfreqs": "docf,arf,aldf", "reldocf": 1, "format": "json"}
                raw_path = raw_dir / f"{stem}.json.gz"
                if args.resume and raw_path.exists():
                    with gzip.open(raw_path, "rt", encoding="utf-8") as handle:
                        envelope = json.load(handle)
                    if envelope["params"] != params:
                        raise ValueError(f"Cached settings differ for {stem}")
                    payload = envelope["response"]
                else:
                    print("Extracting", stem, flush=True)
                    payload = client.get("/search/extract_keywords", params)
                    envelope = {"retrieved_at_utc": utc_now(), "endpoint": "/search/extract_keywords",
                                "params": params, "response": payload}
                    with gzip.open(raw_path, "wt", encoding="utf-8") as handle:
                        json.dump(envelope, handle, ensure_ascii=False)
                rows = validate(payload, params, token_counts)
                signature = {r["item"]: tuple(r[k] for k in COLUMNS if k != "score") for r in rows}
                if n == 1:
                    baseline[label, kind] = signature
                elif baseline[label, kind] != signature:
                    raise ValueError(f"Candidate set or frequency metrics changed across N for {label} {kind}")
                csv_path = output / f"{stem}.csv"
                digest = write_csv(csv_path, rows)
                run = {"file": csv_path.name, "raw_response": str(raw_path.relative_to(output)),
                       "retrieved_at_utc": envelope["retrieved_at_utc"], "params": params,
                       "row_count": len(rows), "reported_total": payload["total"],
                       "score_gt_1_rows": sum(r["score"] > 1 for r in rows),
                       "sha256": digest, "validation": "passed"}
                manifest["runs"].append(run)
                write_json(manifest_path, manifest)
                print(f"Saved {csv_path.name}: {len(rows):,} rows; validated.", flush=True)
    manifest["status"] = "complete"
    manifest["completed_at_utc"] = utc_now()
    write_json(manifest_path, manifest)
    print("Completed all 16 exports.", flush=True)


if __name__ == "__main__":
    main()
