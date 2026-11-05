# Roadmap and proposed structure

## Objective and success criteria

Build a reproducible project that helps buyers compare housing trade-offs. Deliver a documented dataset, interpretable findings, a tested current-price model, and an interactive prototype. Success means a reader can reproduce the analysis, understand how the model was evaluated, inspect comparables, and see the limits of the result. Define numerical quality thresholds after the first data audit, before choosing the final model.

## Phase 0: Data audit and design

Initial audit results are in [phase0-audit.md](phase0-audit.md). Downloads, profiling and [coordinate validation](coordinate-validation.md) have been run. [Historical transport decisions](transport-history.md) support dated MRT service availability with conditional location proxies; historical exit/bus/LRT/routing features remain excluded. The [modelling dataset and chronological splits](model-dataset.md) are prepared. Authenticated routing performance and model acceptance criteria remain open.

- Inspect HDB transaction schemas, date range, duplicates, nulls and anomalous prices; document older dataset changes.
- Obtain HDB property information and investigate building polygons or OneMap for block matching. Test a sample, calculate match rates and inspect errors; preserve unmatched records and their exclusion reasons.
- Inspect LTA station/exit and bus-stop/route files, keys, licences, coordinates, and actual access. Identify time-stamped historical infrastructure; record gaps.
- Define unit of analysis, target, as-of date, refresh strategy, licensing and reproducibility. Confirm research questions and sketch an app journey.
- Deliver: source inventory, feasibility and quality report, proposed data dictionary, unresolved decisions.

## Phase 1: Analysis and machine learning

[Training-only exploratory analysis](eda-findings.md) is complete for the current snapshot. Executable analysis is in `analysis/`; aggregate tables and charts are in `reports/eda/`. Station age and station-opening effects remain untested. Baseline development and model validation are next.

- Clean transaction and block data; create reproducible transforms and geographic features using a suitable projected coordinate system. Label straight-line distances honestly.
- Investigate price distributions over time, town, flat type, lease, floor area and transport proximity. Avoid interpreting associations as causal effects.
- Split by transaction time. Compare a simple recent local median baseline, a regularised regression baseline and a tree-based model. Fit preprocessing only on training data.
- Report MAE in S$, median absolute error and error by town, flat type, price band and time; report sample counts. Reserve the latest period as final test, using earlier rolling time windows for model selection.
- Compare models with and without transport features on the same holdout. Use historical infrastructure only where dates can be substantiated; otherwise restrict those features or omit them for historical model training.
- Investigate uncertainty intervals on held-out data, including observed coverage; do not present an unvalidated range as a calibrated prediction interval. Develop a comparable-sales method and flag insufficient matches.
- Deliver: reproducible analysis, evaluation and limitations, model artefact and feature definitions; report whether transport improves performance.

## Phase 2: Resale explorer web app

### Explore the data page (planned)

- Add a separate historical transaction explorer alongside the shortlist/price-estimate experience. Present a documented, cleaned view of the public transaction records, with source, refresh date, field definitions and data limitations; keep original downloads in the reproducible pipeline.
- Filter by transaction period, town, flat type, floor area, remaining lease and storey range. Use flat type initially: HDB room labels are not bedroom counts, and the current resale source has no explicit bedroom-count field. Only add a bedroom filter if a reliable mapping or source can support it, clearly marking inferred values.
- Show a line chart of monthly/quarterly median gross price or median S$/m², with transaction counts. Let users compare a few towns or flat types; keep gross prices and S$/m² clearly separated. Warn that changing transaction mix can change medians.
- Add transaction scatterplots: floor area or remaining lease versus gross price, coloured by flat type, and optionally transactions over time with a median overlay. Use transparency, aggregation or a clearly disclosed sample for dense plots; compute counts and summaries from the full filtered selection.
- Add a sortable town comparison, defaulting to lowest median S$/m² first for affordability, with a highest-first option. Include counts and a chosen time window; avoid presenting pooled town medians as model-adjusted location effects.
- Provide a paginated transaction table with the same active filters. Hover details can show transaction month, block/street, flat type, area, reported floor range, lease and recorded price; no exact unit, current availability or unobserved condition should be inferred. Review source terms before enabling filtered downloads.
- Keep filters consistent across charts and table, show active filters, reset controls, units and sample counts, and handle empty/small selections explicitly. Use clear chart labels and an accessible table alternative.
- Keep research and public reporting separate: development EDA stays training-only. A later public historical explorer can display the approved full dataset after final model evaluation is frozen; it must not become a route for tuning against the final test period. Historical summaries remain distinct from predictions and live listings.

### Other app capabilities

- Prototype a Python app (e.g. Streamlit) with area, budget, flat type and lease filters, a map with MRT and bus stops, and recent transactions.
- Add independent, combinable location filters: (1) Near family / PHG, using a parent or child's address and an approximate 4 km straight-line preset; and (2) Near a place, using an address or postcode and a user-selected radius. Show both areas and highlight matching blocks in the overlap. Resolve and confirm addresses; handle unmatched results.
- Link the family filter to HDB's official distance enquiry. The app's radius is approximate and neither verifies HDB's distance method nor determines PHG eligibility; prompt users to check shortlisted blocks with HDB, especially near the boundary.
- Investigate a public-transport commute filter for Near a place, including destination, departure day/time and maximum journey time. Test OneMap routing availability, quotas, costs, coverage and performance before offering it for many blocks; clearly identify estimates and errors. Commute time is not a straight-line radius.
- Add flat-input price estimation, comparable sales, data-as-of dates, distance methodology, uncertainty and model limitations. Design for small screens and accessible labels.
- Verify that app inputs use the exact same preprocessing and units as training. Test missing inputs, low-data areas, model loading, map interaction and representative user journeys.
- Deploy only after checking hosting, source attribution, data refresh, third-party terms, privacy and running costs. No live listings unless an authorised source is separately obtained.
- Deliver: usable prototype, deployment instructions and project walkthrough.

## Phase 3: BTO and future planning

- Add user-entered BTO price, estimated completion date, optional interim housing and renovation budgets; compare with resale now and resale later on a timeline.
- Show price, timing and costs separately; do not treat mortgage principal as an expense or call a price difference profit. Do not determine eligibility, grant entitlement or loan approval; link to HDB.
- Add a grant discovery guide, separate from the price model, for household circumstances and new/resale choices. Show potentially relevant grants, conditions, official HDB links and last-reviewed dates; mark missing information clearly. Initial version does not calculate eligibility or grant amounts. Allow an optional user-entered grant amount, ideally from an HFE assessment, in comparisons; keep gross purchase price and other costs visible.
- Treat addresses, household status and financial inputs as sensitive; collect only what is needed, explain whether a postcode is sent to a geocoding provider and avoid storing inputs by default. Connect the PHG guidance to the family filter and HDB's official distance check.
- Provide editable, clearly hypothetical future growth scenarios, with assumptions and the appropriate remaining lease at the future date. Do not present scenario bands as probabilities.
- Independently assess forecasting using rolling-origin tests for each horizon (e.g. 1 and 4 years), comparing no-change and historical-trend baselines; use only information known at each forecast date. Describe the changing mix of flats in aggregated forecasts.
- Ship a modelled forecast only if data, backtests, uncertainty and usability justify it; otherwise retain scenarios only.
- Deliver: comparison view, explanation of assumptions and forecast evaluation report.

## Phase 4: Refinement and documentation

- Review accuracy and data refresh, improve accessibility, document failures and decisions, and add carefully selected amenities and improve commute features if reliable data and access permit.
- Publish a concise case study describing the problem, sources, methodology, findings, measured errors and limitations, plus screenshots/demo.

## Proposed repository structure

This is a target structure; folders should be created as implementation begins, not mistaken for completed code.

```text
sg-flats/
├── README.md
├── docs/
│   ├── roadmap.md
│   ├── data-sources.md
│   ├── data-dictionary.md       # planned
│   └── model-report.md          # planned
├── data/
│   ├── raw/                     # local, ignored; source snapshots
│   ├── interim/                 # local, ignored
│   └── processed/               # local, ignored
├── notebooks/                   # exploratory analysis
├── src/hdb_explorer/
│   ├── data/                    # acquisition and cleaning
│   ├── features/                # geographic and other features
│   ├── modeling/                # training, evaluation, inference
│   └── comparables/             # comparable-sale selection
├── app/                         # planned Streamlit interface
├── models/                      # generated artefacts, normally ignored
├── tests/                       # meaningful data and prediction checks
├── reports/                     # figures and findings
├── pyproject.toml               # dependencies and project configuration
├── .env.example                 # names only; never secrets
└── .gitignore
```

Data snapshots, derived datasets and model files should only be shared after checking applicable terms and size limits. Keep API keys out of git. The final implementation can simplify this structure as appropriate.
