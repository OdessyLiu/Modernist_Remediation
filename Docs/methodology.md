# Methodology

## Methodological Overview

This study uses a **corpus-assisted mixed interpretive approach** to investigate readerly expectations in Goodreads reviews of graphic biographies.

The workflow combines:

- corpus description;
- evaluative comparison;
- keyword and keyness analysis;
- collocation and concordance analysis;
- expectation-marker analysis;
- qualitative reading of review context.

The purpose of computational analysis is to identify recurrent patterns that can be interpreted in relation to reader evaluation and expectation.

The general workflow is:

> corpus description → comparative lexical analysis → contextual inspection → expectation-domain construction

Analytical categories should be grounded in corpus evidence rather than imposed in advance wherever possible.

---

## 1. Corpus Description

The first stage establishes the structure and limitations of the corpus before inferential or comparative analysis begins.

### Corpus-Level Measures

Report:

- number of books;
- number of reviews;
- number of reviewers, where identifiable;
- total token count;
- vocabulary size where useful;
- mean and median review length;
- review-length distribution;
- star-rating distribution;
- temporal distribution of reviews where dates are available.

### Book-Level Measures

Report:

- number of reviews per book;
- token count per book;
- star-rating distribution by book;
- mean or median review length by book;
- contribution of each book to the full corpus.

These measures are used to identify books that disproportionately influence corpus-level patterns.

### Reviewer-Level Measures

Where stable reviewer identifiers are available, report:

- number of reviews per reviewer;
- proportion of reviews contributed by highly active reviewers;
- concentration of corpus tokens by reviewer.

Reviewer-level analysis is important because repeated contributions from a small number of users may distort apparent lexical patterns.

### Distribution and Concentration

Where relevant, analytical outputs should record whether a lexical pattern is broadly distributed or concentrated in particular:

- books;
- reviewers;
- time periods.

Raw frequency alone should not be interpreted as evidence of a corpus-wide tendency.

---

## 2. Text Preparation

Preprocessing should preserve as much interpretive value as possible.

At minimum:

- retain the original review text;
- preserve book, review, reviewer, rating, and date identifiers where available;
- create processed text as a derived field rather than replacing original text;
- document tokenization and normalization procedures;
- document exclusions and filtering.

Potential preprocessing steps may include:

- Unicode normalization;
- whitespace normalization;
- tokenization;
- lowercasing for lexical counting;
- lemmatization where analytically justified;
- removal of non-linguistic artifacts.

Stopword removal should not be applied automatically to analyses involving expectation or evaluative constructions because function words, negation, modality, and intensifiers may carry important interpretive information.

---

## 3. Evaluation Measures

Evaluation should be operationalized using multiple signals rather than a single measure.

### Star Rating

Goodreads star ratings provide explicit platform-level evaluation.

Star rating can be used to construct comparative subsets such as:

- higher-rated reviews;
- lower-rated reviews.

The exact threshold should be documented and justified.

Middle ratings may be:

- retained as a comparison group;
- excluded from polarized high/low comparisons;
- analyzed separately.

This choice should depend on the analytical question rather than convenience.

### Textual Valence

Textual valence may be estimated separately from star rating using an interpretable sentiment method or another validated procedure.

Textual valence should not be assumed to equal:

- star rating;
- evaluation;
- reader expectation.

Instead, it can be used to investigate:

- agreement between rating and review language;
- disagreement or mixed evaluation;
- evaluative passages within reviews with similar ratings.

### Relationship Between Signals

Before combining star rating and textual valence, examine their relationship empirically.

Potential analyses include:

- correlation;
- cross-tabulation;
- disagreement cases;
- distribution of textual valence within each star rating.

A combined evaluation measure should only be created if there is a clear methodological reason.

### Shelving and Other Metadata

Goodreads shelving or categorization data may provide useful contextual information, but should not be incorporated into the evaluation measure without a separate conceptual justification.

At present, shelving should be treated as a possible supplementary variable rather than a finalized component of evaluation.

---

## 4. Keyness Analysis

Keyness analysis is used to identify lexical items that are unusually prominent in one corpus or subcorpus relative to another.

Two comparisons are of primary interest.

### A. Graphic-Biography Corpus vs Reference Corpus

Where a suitable reference corpus is available, this comparison can identify language unusually characteristic of discourse surrounding graphic biographies.

The reference corpus must be selected and documented carefully because keyword results depend strongly on the comparator.

### B. Higher- vs Lower-Evaluation Reviews

This comparison is used to identify lexical differences associated with contrasting reader evaluations.

Its purpose is not simply to produce lists of positive and negative words. It is used to locate candidate evaluative criteria and reader concerns.

### Keyword Reporting

For keyword candidates, retain where possible:

- raw frequency;
- normalized frequency;
- keyness statistic;
- effect-size measure;
- dispersion across books;
- dispersion across reviewers.

Statistical significance alone should not determine interpretive importance.

### Candidate Selection

Analysis may inspect ranked sets such as the top:

- 30;
- 100;
- 200

keywords, depending on the purpose of the analytical stage.

These are inspection ranges, not predetermined final reporting thresholds.

---

## 5. Corpus-Driven Interpretation of Keywords

Keyword lists are treated as starting points for interpretation.

For analytically important terms:

1. inspect frequency and dispersion;
2. inspect major collocates;
3. examine concordance lines;
4. inspect a sample of complete reviews;
5. identify recurring evaluative uses;
6. group related patterns into provisional semantic or evaluative domains.

For example, words associated with:

- detail;
- depth;
- history;
- information;
- art;
- illustration;
- story;
- emotion;
- pacing;

should not be assigned to a domain based on lexical meaning alone.

Their function must be established through contextual evidence.

### Domain Construction

Evaluative or expectation domains should be developed inductively from recurring contextual patterns.

Possible domains may eventually include:

- biographical depth;
- historical information;
- educational value;
- narrative structure;
- emotional engagement;
- visual representation;
- accessibility;
- completeness.

These remain provisional until supported by corpus evidence.

Each domain should be documented with:

- defining principle;
- representative lexical patterns;
- example constructions;
- ambiguous or excluded cases.

---

## 6. Collocation and Concordance Analysis

Collocation analysis is used to examine the lexical environments of important evaluative or expectation-related words.

Possible targets include:

- `expected`;
- `wanted`;
- `more`;
- `less`;
- `enough`;
- `depth`;
- `detail`;
- `art`;
- `story`;
- `informative`.

The specific association measure and window size should be documented.

Collocation analysis should be followed by concordance inspection because statistical co-occurrence does not determine semantic function.

Concordance analysis is used to examine:

- polarity;
- negation;
- modality;
- grammatical patterns;
- repeated evaluative constructions;
- what aspect of the book is being evaluated.

Full-review reading should be used where a concordance line is insufficient for interpretation.

---

## 7. Expectation-Marker Analysis

A complementary analysis will identify language that more directly signals reader expectations.

### Initial Marker Set

Candidate markers may include constructions involving:

- `expect`;
- `expected`;
- `expecting`;
- `want`;
- `wanted`;
- `wish`;
- `wished`;
- `hope`;
- `hoped`;
- `should`;
- `should have`;
- `could have`;
- `more`;
- `less`;
- `too`;
- `enough`;
- `not enough`;
- `needed`;
- `missing`;
- `surface level`;
- `introduction`.

This is a seed set rather than a finalized lexicon.

### Contextual Validation

Occurrences should not automatically be classified as expectations.

For each marker, inspect concordances to distinguish genuine expectation-related use from unrelated grammatical or semantic uses.

For example:

- "I wanted more historical context" → explicit unmet expectation.
- "I wanted to read this book for years" → reading intention, not an expectation about the book.
- "more than 200 pages" → quantitative description, not evaluation.

Validated constructions can then be grouped according to:

- expected feature;
- direction of expectation;
- fulfillment status;
- evaluative domain.

### Possible Expectation Types

The analysis may distinguish:

- explicit prior expectation;
- retrospective normative expectation;
- desire for more;
- desire for less;
- expectation fulfillment;
- expectation violation;
- comparative expectation.

These categories should be refined through corpus inspection.

---

## 8. Relationship Between Evaluation and Expectation

A major analytical goal is to determine how specific expectations relate to broader evaluations.

Questions may include:

- Which expectation domains occur disproportionately in lower-rated reviews?
- Which expectations appear in positive reviews as successfully fulfilled?
- Do the same criteria appear in both praise and criticism?
- Which expectations generate mixed or contested evaluations?
- Are some expectation domains concentrated in particular books?

This stage should avoid treating correlation as causation.

The analysis can establish that certain evaluative criteria co-occur with ratings or valence, but not necessarily that those criteria caused the rating.

---

## 9. Qualitative Verification

Computational outputs should be verified through close inspection of source reviews.

For major findings:

- inspect concordance evidence;
- read representative full reviews;
- inspect counterexamples;
- check multiple books;
- check multiple reviewers;
- note ambiguous cases.

Interpretations should not rely on isolated quotations or a single unusually prolific reviewer.

Where appropriate, maintain a small audit sample documenting how computational patterns were translated into interpretive categories.

---

## 10. Exploratory and Confirmatory Status

Most analyses in this project are exploratory.

Exploratory steps include:

- discovering keyword candidates;
- identifying collocational patterns;
- constructing expectation domains;
- refining the expectation-marker lexicon.

Once categories are established, later analyses may test their distribution more systematically.

The distinction between:

- **category discovery**
and
- **category measurement**

should remain explicit.

The same data should not be treated as independent validation evidence when it was used to create the category being tested.

---

## 11. Reproducibility and Reporting

All analytical procedures should document:

- corpus version;
- inclusion and exclusion criteria;
- preprocessing;
- subset definitions;
- normalization;
- statistical measures;
- thresholds;
- sampling procedures;
- lexicon versions;
- manual coding rules.

Derived datasets and results should be reproducible from preserved source data and analysis scripts.

Where feasible, outputs should preserve identifiers that allow any aggregate result to be traced back to:

- a book;
- a reviewer;
- a review;
- the original review text.

---

## 12. Interpretation Principle

Throughout the project, computational evidence should answer progressively more specific questions:

> **What language is prominent?**

→

> **What is that language doing in review context?**

→

> **What criterion is the reader using to evaluate the book?**

→

> **What does that criterion reveal about readerly expectations for graphic biography?**

This progression is the methodological core of the project.