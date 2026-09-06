# ModernistRemediation

This repository supports a computational literary studies project on **readerly expectations of graphic biographies**, using Goodreads reviews as reception data.

## Research Focus

The study has two primary objectives:

1. Describe how readers evaluate and articulate expectations of graphic biographies.
2. Explore interpretable computational methods for identifying evaluative and expectation-related language in online reader reviews.

The main theoretical focus is **readerly expectation as one dimension of genre formation**. Goodreads reviews provide evidence of reception and reader expectations; they should not be treated as direct evidence of textual genre conventions or production practices.

## Project Documentation

Before making methodological assumptions or substantial analytical changes, read:

- `README.md` — current data, scripts, outputs, and implemented analyses.
- `docs/research-context.md` — research questions, theoretical framework, and corpus rationale.
- `docs/methodology.md` — current analytical design and methodological decisions.

When documentation and code differ, identify the discrepancy rather than silently choosing one.

## Analytical Principles

- Distinguish **evaluation**, **textual valence**, and **reader expectation**; do not treat them as interchangeable.
- Do not assume star ratings fully represent the evaluative meaning of review text.
- Interpret lexical patterns in context using collocations, concordances, and full reviews where appropriate.
- Prefer interpretable corpus-linguistic measures when they can answer the research question.
- Check whether apparent corpus patterns are concentrated in particular books or reviewers.
- Treat exploratory categories and lexicons as provisional until validated against review context.
- Do not convert tentative methodological ideas into finalized procedures without explicit instruction.

## Data and Reproducibility

- Never modify or overwrite raw data.
- Preserve book, review, and reviewer identifiers through analytical workflows where available.
- Make filtering, exclusion, sampling, and preprocessing decisions explicit.
- Report both raw counts and normalized measures where appropriate.
- Save derived data and analytical outputs separately from source data.
- Prefer reproducible scripts over manual transformations.

## Coding

- Inspect existing code before creating parallel implementations.
- Make the smallest change necessary for the requested task.
- Preserve existing analyses unless explicitly asked to replace them.
- Keep analytical code readable and modular.
- Document new metrics, outputs, dependencies, and methodological assumptions.

When a task involves an ambiguous methodological choice, surface the choice and its consequences instead of silently resolving it.