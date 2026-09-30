# XML review corpus

Run `python3 Analysis/Reviews_XMLCorpus.py` from the repository root (Python standard library only). Optional `--input` and `--output` arguments override paths.

The source is `Data/Reviews/AllReviews_217_VA.json`; no file named `AllReviews_217_VAS.json` was present. The derived output is `Data/Reviews/XML/AllReviews_217_VA.xml`. Re-running replaces this export without modifying the source.

The XML has one `<corpus>` root and one `<doc>` per review, preserving source order. Each document contains the review text and exactly these attributes:

| Attribute | Source or rule |
|---|---|
| `review_id` | Source `index`, a corpus-local unique identifier, not a Goodreads review ID |
| `book_id` | Stored `book_id`, unchanged |
| `reviewer_id` | Numeric user ID extracted from `reviewer_url` |
| `rating` | Integer star rating, or an empty string for null |
| `rating_group` | `high` (4–5), `low` (1–2), `middle` (3), `no_rating` (null), following the existing rating partition |

No other source fields are exported. No reviews are filtered, sampled, deduplicated, or reordered. Rating groups describe stars, not textual valence or reader expectations.

XML serialization escapes markup symbols such as `&`, `<`, and `>` while preserving their text values when parsed. Unicode and whitespace are retained, including carriage returns via character references. Only characters forbidden by XML 1.0 are removed, with a count printed at execution. The script checks unique review identifiers, rating values, extracted reviewer identifiers, exact text and attribute round trips, review count, and unchanged source bytes; it also parses the written file.

The initial export contains 17,967 reviews: 11,493 high, 1,593 low, 4,287 middle, and 594 without ratings. No invalid XML characters required removal. Source SHA-256: `fc1a6cb2e2361ee3e9cd407215cca04d2accc64d42d78e27f59862684bf83017`.
