# Phase 0: Initial data audit

Audit date: 5 November 2026 (Singapore time). Status: initial snapshot audit completed. A subsequent [coordinate validation](coordinate-validation.md) assigns all addresses with confidence tiers, and [transport history review](transport-history.md) defines which features are supported. Authenticated route-time testing remains open. The findings below preserve the initial audit stage. No price model or app has been built.

## Findings

| Check | Observed result | Decision |
|---|---|---|
| Resale snapshot | 244,230 rows, 11 columns; January 2017–November 2026, no missing months | Suitable starting point for analysis; retain the raw snapshot locally. |
| November 2026 | 358 transactions in an in-progress month, versus 2,175 in October | Exclude the in-progress month from monthly trend comparisons and evaluation until a later refresh. Other recent months may also be revised; do not assume finality. |
| Required source fields | No blank values; numeric price/area/lease-year fields parse; no non-positive prices or areas | Passes these basic checks, not proof that every record is correct. |
| Repeated complete rows | 318 rows repeat earlier rows | Retain for now: no transaction ID or unit number is available to distinguish separate identical sales. Assess sensitivity later. |
| Remaining lease / storey | All remaining-lease values and storey ranges parse; no reversed ranges | Derive lease months and storey bounds; storey is a range, not exact unit floor. |
| Property snapshot | 13,392 rows, 24 columns; no repeated block/street keys or blank values | A many-transactions-to-one-property join is feasible. |
| Property join | 244,227 / 244,230 rows (99.9988%); 9,768 / 9,769 distinct addresses | Only `82 MACPHERSON LANE` is unmatched (3 transactions). Preserve and investigate it. |
| Building geometry | 13,436 features: 13,426 Polygon and 10 MultiPolygon; 13,436 unique postcodes | Geolocation candidate source, not yet a verified transaction-coordinate join. |
| LTA station download | 234 Polygon features, 225 distinct station labels | Despite catalogue wording about point locations, downloaded geometry is polygon. Labels include records requiring classification, repeated labels and interchange forms. Do not equate feature count to operating stations. |
| LTA station exits | 613 Point features for 188 distinct station-name labels; 9 repeated station-name/exit-code pairs | Promising for access-distance calculations; historical validity and station coverage still need verification. |
| LTA bus stops | 5,205 Point features, 5,205 distinct stop codes; all status values `OP` | No repeated stop codes in this snapshot. Do not interpret service-type codes without a codebook. |

Computed results are in [the audit summary](../reports/phase0/audit-summary.json), [monthly counts](../reports/phase0/monthly-counts.csv), and [unmatched addresses](../reports/phase0/unmatched-property-addresses.csv). These are computed profiles, not model results.

## Numeric ranges and records requiring review

- Prices range from S$140,000 to S$1,818,000 across the entire period; the pooled median is S$505,000. This pooled median is not an estimate for a flat today.
- Floor area ranges from 31 to 366.7 sqm. The largest record is a Terrace-model flat at `53 JLN MA'MOR`; do not delete it just because it is large. See [largest-floor-area records](../reports/phase0/largest-floor-areas-review.csv).
- Remaining lease ranges from 469 to 1,173 months. No lease commencement year is later than the transaction year.
- Coverage includes 26 towns and seven flat types. `1 ROOM` and `MULTI-GENERATION` have only 89 and 93 rows respectively across the snapshot; they need separate evaluation or an explicit scope decision.

## Coordinate matching gap

The transaction/property files have street names. Building polygons instead contain `BLK_NO`, `ST_COD`, and `POSTAL_COD`, without a street name. Block number alone is ambiguous across Singapore. A postcode cannot directly join to the transaction file because that file does not contain one.

We generated a small [candidate-pair sample](../reports/phase0/coordinate-candidates-unverified.csv) using block numbers unique within each source. Those are unverified candidates, not accepted address matches or evidence of coordinate accuracy. We still need a reliable street-code/name bridge or authenticated geocoding and a geographically varied validation sample, including ambiguous and unmatched addresses.

An additional official LTA Road Section Line download was inspected because its catalogue description mentions road names and codes. Its 15,354 records contain `RD_CD` but no road-name field. It does not by itself solve this bridge and is retained as a researched alternative rather than an adopted join source.

## Transport geometry and time

The downloaded LTA shapefiles identify a projected SVY21 coordinate system in metres. The audit reads each `.prj` and transforms extent corners to WGS84 as a sanity check. Actual distance calculations should use validated geometry and compatible projected coordinates. No block-to-station distance has yet been produced.

Station polygon labels include examples such as `SMD`, `UPD` and `DT16 / CE1`; a station-code/name crosswalk and classification are needed before measuring passenger access. Exits may provide a more practical destination point, but their operating status must be checked. Record creation and last-update dates are administrative metadata and must not be used as station-opening dates.

The snapshots do not establish which stations, exits, stops or routes were available at each historical sale date. Consequently, current transport geometry can be investigated for today's explorer, but is not approved as an as-of-sale model feature. A time-valid network or a restricted modelling window must be established first.

## Access tests and terms

- HDB CSVs and building GeoJSON, plus LTA station, exit, bus-stop and road-section ZIPs, downloaded without account credentials. The scripts use data.gov.sg's documented download endpoints and LTA catalogue links.
- A single OneMap search using the public example postcode returned HTTP 200 and a result, but also an authentication-token-missing message. Official documentation requires a token. Do not treat this as stable anonymous access or perform bulk geocoding without the documented credentials.
- An unauthenticated probe to the LTA `BusStops` endpoint returned HTTP 404. This does not establish whether an authenticated request will work. The static bus-stop geometry is available independently; current routes/services and routing need proper access tests.
- OneMap public-transport routing has not been exercised with a valid token. Quotas, response times, date/time coverage, cost and feasibility of filtering many blocks remain unverified.
- Use source attribution and link to the [Singapore Open Data Licence](https://data.gov.sg/open-data-licence). Review [LTA API terms](https://datamall.lta.gov.sg/content/datamall/en/api-terms-of-service.html) and source-specific conditions before enabling APIs or redistributing data. Raw data remains git-ignored; committed reports include source hashes and aggregate findings.

## Reproduce

Tested with Python 3.9 on macOS, with `curl` installed:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-audit.txt
.venv/bin/python scripts/download_phase0.py
.venv/bin/python scripts/audit_phase0.py
```

Downloads are cached under `data/raw/`. Use `--refresh` explicitly to replace them. API download links expire and are never written to the committed manifest; source IDs, retrieval times, file sizes and SHA-256 hashes are retained in [the manifest](../reports/phase0/source-manifest.json). Re-downloading a changing source may produce different results; hashes identify the audited snapshots but do not archive the source data. LTA date-specific filenames are pinned to those observed during this audit and will need review on refresh. A missing remote file should be investigated rather than silently substituted.

## Decisions and next actions

1. Start the first model at the registered-transaction level, targeting `resale_price` in S$. Price-per-sqm can be an analytical measure; avoid target-derived input leakage.
2. Use the 2017-onward transaction file first. Older files and their approval/registration-date differences remain a source review, not an audited combined history.
3. Keep an unmodified snapshot; record transformations and exclusion reasons. Do not discard repeated rows or rare models without analysis.
4. Resolve the coordinate bridge and validate a varied address sample before publishing map results or proximity distances. Do not fuzzy-match ambiguous blocks silently.
5. Obtain and validate a station crosswalk and opening-date history; investigate bus-stop history. Until then, baseline modelling can use transaction attributes without current infrastructure features.
6. Define final chronological train/validation/test dates after reviewing counts and recent-month stability, before model selection. Fit all preprocessing on training data only; test separately on unseen blocks where practical.
7. Record MAE/median absolute error in S$, error by segment, comparable counts and any interval coverage. Accept a richer model only if it improves the chosen baseline on held-out periods without hiding weak segments. Set numerical gates before fitting the final model; this audit does not establish an achievable error target.
8. Test authenticated routing before promising a 30-minute commute filter. Build independent family and custom-radius filters first once coordinates are validated. Link PHG exploration to HDB's official check.

## Initial user journey

Budget, flat type and lease preferences → optional family radius → optional workplace/place radius (later, commute time) → matching blocks and historical transactions → chosen flat's comparables and indicative estimate → optional BTO/grant planning. Grant and PHG guidance remain separate from price modelling and official eligibility decisions.
