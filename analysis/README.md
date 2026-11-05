# Exploratory analysis

Run `python analysis/run_training_eda.py` from the repository root after preparing the modelling dataset. Uses the audit dependencies; no plotting dependency or API token is required.

The script first selects `split == train` and then calculates all price summaries and charts. It does not analyse validation/test prices. Generated aggregate tables, standalone SVG charts and a reproducibility manifest are in `reports/eda/`; interpretation and the exploratory hypothesis register are in `docs/eda-findings.md`.

These are descriptive comparisons, not causal estimates or model performance. EDA is data-informed; hypotheses are exploratory rather than preregistered confirmatory tests.
