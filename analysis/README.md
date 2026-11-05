# Exploratory analysis

Run `python analysis/run_training_eda.py` from the repository root after preparing the modelling dataset. Uses the audit dependencies; no plotting dependency or API token is required.

The script first selects `split == train` and then calculates all price summaries and charts. It does not analyse validation/test prices. Generated aggregate tables, standalone SVG charts and a reproducibility manifest are in `reports/eda/`; interpretation and the exploratory hypothesis register are in `docs/eda-findings.md`.

These are descriptive comparisons, not causal estimates or model performance. EDA is data-informed; hypotheses are exploratory rather than preregistered confirmatory tests.

## Scope and next work

The first script covers transaction time, type, town, area, lease, storey and MRT proxies. It is partial EDA, not an evaluation of all buyer factors. [Buyer needs](../docs/buyer-needs.md) and the [amenity audit](../docs/amenity-audit.md) now govern the follow-up: gross-price relationships, unusual-record distributions, recent training trends, local-comparable support, and historically supported school/food/grocery/park features. No amenity pipeline is implemented yet. Model training is paused pending the documented scope review. Preserve frozen audit outputs and training-only exploration; do not overwrite source manifests when adding new snapshots.
