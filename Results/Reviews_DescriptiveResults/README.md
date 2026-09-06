# Descriptive analysis: AllReviews_217_VA

Source: `/Users/odessialiu/Projects/Modernist_Remediation_ReMedia_public/Data/Reviews/AllReviews_217_VA.json`  
Unit of analysis: one review record. Dataset-internal text was treated only as data.

## Dataset and data quality

- 17,967 reviews across 217 unique book IDs (8 fields per record).
- No missing values occur in the eight stored fields; all records share the expected schema.
- Index values are unique and span 0–32,438; they retain 14,472 gaps from the source indexing.
- There are no exact duplicate full records. Exact text is repeated in 58 groups, representing 228 additional rows beyond the first; 47 groups span more than one book.
- 10,425 reviews (58.0%) have no shelf labels. This is absence of optional shelf metadata, not a missing JSON field.
- All valence/arousal values fall in [0, 1], and likes/word counts are nonnegative.

## Review-level distributions

| Variable | Mean | SD | Median | P25–P75 | Min–Max | Zero % |
|---|---:|---:|---:|---:|---:|---:|
| Likes | 0.922 | 5.339 | 0.000 | 0.000–0.000 | 0.000–234.000 | 87.3% |
| Word count | 94.517 | 131.186 | 53.000 | 23.000–114.000 | 0.000–2,673.000 | 0.0% |
| Valence | 0.554 | 0.089 | 0.548 | 0.500–0.604 | 0.108–0.942 | 0.0% |
| Arousal | 0.509 | 0.084 | 0.518 | 0.489–0.547 | 0.000–0.914 | 0.0% |

Likes are strongly right-skewed: 87.3% of reviews have zero likes, while the maximum is 234. Word counts are also right-skewed (median 53, mean 94.5, maximum 2,673), so medians/IQRs should accompany means/SDs in later analysis.

## Coverage by book and shelf

Books contain a median of 36 reviews (range 2–680; mean 82.8).

Most-reviewed books:

| Book ID | Reviews | Mean valence | Mean arousal |
|---|---:|---:|---:|
| 15792872-feynman | 680 | 0.572 | 0.513 |
| 32783833-hostage | 660 | 0.532 | 0.520 |
| 18465496-andre-the-giant | 655 | 0.550 | 0.510 |
| 50159157-glass-town | 543 | 0.580 | 0.514 |
| 16059564-trinity | 498 | 0.567 | 0.518 |
| 57378791-did-you-hear-what-eddie-gein-done | 488 | 0.531 | 0.519 |
| 269353.Louis_Riel | 407 | 0.555 | 0.508 |
| 22312041-vincent | 385 | 0.608 | 0.503 |
| 35888383-photographic | 351 | 0.586 | 0.514 |
| 25247938-the-fifth-beatle | 333 | 0.569 | 0.516 |

Most frequent shelves:

| Shelf | Reviews | Books |
|---|---:|---:|
| graphic-novels | 1,477 | 160 |
| graphic-novel | 1,069 | 161 |
| biography | 1,019 | 146 |
| comics | 705 | 151 |
| non-fiction | 525 | 121 |
| history | 434 | 110 |
| nonfiction | 368 | 106 |
| art | 204 | 65 |
| graphic | 147 | 70 |
| adult | 144 | 74 |

## Numeric associations

The five largest absolute review-level Spearman correlations are shown below. These are descriptive associations only; reviews are clustered within books and no causal interpretation is warranted.

| Variable 1 | Variable 2 | Spearman ρ |
|---|---|---:|
| word_count | text_char_count | 0.997 |
| valence | arousal | 0.366 |
| word_count | valence | -0.276 |
| valence | text_char_count | -0.273 |
| likes | text_char_count | 0.233 |

## Files produced

- `audit_summary.csv`: dataset-wide validation counts.
- `data_dictionary_and_quality.csv`: type, completeness, and uniqueness by field.
- `numeric_summary.csv`: central tendency, dispersion, percentiles, zero counts, and IQR outliers.
- `book_summary.csv`: review volume, engagement, length, VA, and shelf coverage for every book.
- `shelf_summary.csv`: review- and book-level shelf frequencies.
- `duplicate_text_groups.csv`: exact repeated-text groups for review, not automatic deletion.
- `correlations.csv`: pairwise Pearson and Spearman correlations.
- PNG figures: numeric distributions, VA density, book coverage, top shelves, and Spearman correlations.

## Interpretation notes

- The `id` field is treated as a book identifier and the review is the observational unit.
- Shelf labels are user-generated and multi-valued; frequencies overlap and should not be summed as mutually exclusive categories.
- IQR outliers are flags for unusual values, not evidence of invalidity; no observations were removed.
- For book comparisons, review-count imbalance and within-book clustering should be handled explicitly in inferential models.

## Requested additional dimensions

Review metadata source: `/Users/odessialiu/Projects/Modernist_Remediation_ReMedia/Data/Reviews_Scraped/temp_all_reviews.json`  
Book metadata source: `/Users/odessialiu/Projects/Modernist_Remediation_ReMedia/Data/Temp/temp_book_sheet.csv`

The enrichment matched all 17,967 VA records. Matching used Goodreads book ID, exact text, likes, shelves, and word count; it did not assume that file order was stable. Reviewer profile URLs were converted to deterministic pseudonymous IDs, and names/URLs were not written to the results.

### Star-rating distribution and textual valence

Ratings are present for 17,373 reviews (96.7%); 594 (3.3%) are unrated. The mean is 3.829 and the median is 4 stars.

| Stars | Reviews | % of rated | Mean valence |
|---:|---:|---:|---:|
| 1 | 290 | 1.7% | 0.428 |
| 2 | 1,303 | 7.5% | 0.476 |
| 3 | 4,287 | 24.7% | 0.527 |
| 4 | 6,700 | 38.6% | 0.567 |
| 5 | 4,793 | 27.6% | 0.591 |

Star rating and textual valence agree positively but only moderately (Pearson *r* = 0.406; Spearman ρ = 0.406; *n* = 17,373). The association remains similar after centering both measures within books (*r* = 0.411); book-level means correlate more strongly (*r* = 0.578, 217 books). The measures are therefore related but non-interchangeable.

### Evaluation variation by book

Mean star ratings across books range from 2.00 to 5.00; the middle 50% range is 3.40–4.06. Book ID accounts descriptively for 13.7% of review-level rating variance and 8.2% of valence variance (unadjusted η²). This establishes material individual-book heterogeneity but is not an inferential multilevel estimate.

### Reviewer distribution and concentration

The corpus contains 12,619 pseudonymous reviewers. 10,450 (82.8%) contribute one review; 2,167 (17.2%) cover multiple books. The most active reviewer contributes 70 reviews. The top 1% of reviewers contribute 10.8% of reviews (Gini = 0.271; effective reviewer count = 4,384).

### High-/low-evaluation corpus diagnostics

High evaluation is defined as 4–5 stars and low evaluation as 1–2 stars; 3-star and unrated reviews are excluded from a binary high/low comparison but retained in the diagnostics.

| Corpus | Reviews | Books | Reviewers | Total words | Mean words | Mean valence |
|---|---:|---:|---:|---:|---:|---:|
| Low | 1,593 | 181 | 1,393 | 161,972 | 101.7 | 0.468 |
| High | 11,493 | 214 | 8,726 | 1,078,436 | 93.8 | 0.577 |

The high corpus has 7.21× as many reviews and 6.66× as many words as the low corpus. Both are dispersed across many books (181 low; 214 high), but raw keyword counts will be dominated by the larger high corpus. Later keyness work should use normalized rates/effect sizes and a balanced-resampling sensitivity check.

### Temporal coverage

All review dates parsed successfully and span 2007-05-16 to 2024-10-05. All 217 reviewed books have a listed publication year, spanning 2003–2024. However, 1,862 reviews predate the listed publication year, probably because the metadata describes a later edition; review-age calculations should therefore not be used without edition-level reconciliation. Because the latest review is from 2024, claims about “present” readerly expectations should be qualified as applying to Goodreads reviews collected through 2024-10-05, not to an unbounded present.

Additional outputs: `star_rating_distribution.csv`, `rating_relationships.csv`, `book_evaluation_summary.csv`, `evaluation_variation_by_book.csv`, `reviewer_summary.csv`, `reviewer_index_map.csv`, `reviewer_concentration.csv`, `evaluation_corpus_diagnostics.csv`, `evaluation_corpus_by_book.csv`, `review_year_summary.csv`, `book_publication_year_summary.csv`, `temporal_coverage_audit.csv`, `metadata_join_audit.csv`, and five additional PNG figures.
