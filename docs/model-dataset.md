# Modelling dataset and evaluation design

**Current status:** preparation is a provisional candidate schema. Training is paused pending the [broader amenity audit](amenity-audit.md) and [buyer-needs review](buyer-needs.md). Existing row counts/splits stay fixed; no unaudited amenities have been added. `config/project-status.json` records this status for readers, not as a runtime enforcement mechanism.

The modelling preparation has run successfully on the 5 November 2026 snapshot. No price model has been trained. All 244,230 transactions retain their coordinate assignment and confidence tier.

## Unit, target and time splits

Each row is a registered resale transaction, not a unique flat or live listing. The target is the recorded gross resale price in Singapore dollars. Renovation, grants, financing and asking prices are not target adjustments.

| Split | Transaction months | Records | Purpose |
|---|---|---:|---|
| Training | January 2017–December 2024 | 196,982 | Fit preprocessing and models |
| Validation | January–December 2025 | 25,084 | Choose models, features and settings |
| Final test | January–October 2026 | 21,806 | One final evaluation after choices are frozen |
| Excluded | November 2026 | 358 | Incomplete snapshot month |

Calendar completion does not guarantee that earlier months will never be revised. Refreshes must produce a new manifest and reviewed split configuration. These are snapshot-specific periods, not automatic moving windows.

Freeze this split before modelling. Use expanding windows ending in 2022, 2023 and 2024 within the training/validation period for stability checks, never random row splits. Fit encoders, imputers, scalers, target transformations and comparable-sale reference tables using only the applicable training window. Do not inspect test scores to choose a model. Final reporting should distinguish the original frozen model from any later refit for deployment.

## Feature groups

The machine-readable allowlist is in [model-data.json](../config/model-data.json). Do not train on every column in the output CSV.

- Base features: town, flat type, flat model, floor area, lower/upper storey bounds, remaining lease in months, transaction month index, and SVY21 x/y coordinates.
- Optional transport comparison: nearest operational MRT physical-station proxy distance in metres, measured as straight-line Euclidean distance in EPSG:3414.
- Transport sensitivity: the same distance with service availability lagged one additional month. Registration month can follow price agreement; this sensitivity does not reconstruct agreement dates.
- QA/context only: record ID, address, postcode, nearest station name, coordinate confidence, repeated-row flag, unseen-address flag, original raw columns and split label.

Storey bounds describe a reported range, not an exact floor. Remaining lease uses the source's years/months rather than an inferred 99-year lease. Month index is months since January 2017; it supports historical price estimation, not a validated future forecast.

MRT service enters only from its first full service month. Interchange codes collapse to one physical station. Current station geometry is an explicit historical stability assumption; these are neither entrance distances nor walking/commute times. January 2017's lagged feature uses the known pre-window network rather than pretending December 2016 was fully reconstructed. See [transport decisions](transport-history.md).

Exclude current property counts, current bus/exit/routing features, undated amenities, future infrastructure, price per square metre and target-derived aggregates from the first feature set. A comparable-sales baseline must use past transactions only. Any later target encoding must be time-aware and fitted separately within each training fold.

## Quality and coverage

- All source rows survive the many-to-one coordinate join; no missing model inputs or nonfinite numeric features were found.
- All remaining leases and storey ranges parsed; price, area and lease are positive. Unusual valid categories and large flats are retained for investigation, not silently removed.
- The 318 additional identical source rows are retained: no unit or transaction identifier establishes that they are errors. There are 635 rows in repeated groups. Report a training-only deduplication sensitivity later; do not alter the holdout opportunistically.
- Validation has 825 transactions at addresses absent from training; test has 1,506. Report performance on these subsets as well as town, flat type, month, price band and coordinate confidence, with sample counts.
- Recurring blocks across periods are allowed because the intended task includes pricing flats in known blocks. Exact-unit overlap cannot be assessed from public block-level records; do not claim unseen-property evaluation.
- Coverage reports contain counts only. Test-price summaries and scores have not been used for selection. There is no demonstrated accuracy yet.

## Reproduction and outputs

After running the acquisition, coordinate and transport pipelines described in the linked audit documents:

```bash
python -m pip install -r requirements-audit.txt
python scripts/prepare_model_data.py
```

The generated `data/processed/model-transactions.csv` stays local and ignored. `reports/model-data/summary.json` records SHA-256 input/output hashes, counts and gates; companion CSVs report coverage by month, town, flat type and coordinate confidence. Re-running identical inputs must reproduce the output hash. `record_id` hashes the source file hash and one-based source record ordinal: it is unique within this snapshot, not a permanent transaction identifier across refreshes.

The builder stops on duplicate coordinate keys, incomplete joins, malformed leases/storeys, invalid split boundaries, unexpected excluded months, missing station proxies, missing/nonfinite features or invalid positive values. It does not fit a model, contact an API or read `.env`.

## Next modelling gates

1. First complete the amenity audit restart gate: source/profile evidence, historical-use decisions (including explicit exclusions), broader EDA and reviewed feature list. Then explore training-period distributions, category support and time trends; record transformations before comparing models.
2. Implement a past-only recent local median baseline, regularised regression and a tree model with training-only preprocessing.
3. Compare base, eligible amenity-group additions and transport versions on identical validation windows, including the additional service lag and coordinate-confidence sensitivity.
4. Set practical error and coverage acceptance criteria from the baseline and intended app use before opening final test scores. Evaluate intervals separately; a point model is not a calibrated uncertainty model.
5. Freeze choices, evaluate once on final test, publish subgroup errors and limitations, then decide whether estimates are suitable for a prototype.

Phase 0's routing feasibility work remains separate: it is needed before offering commute filtering, not to train this first price model.
