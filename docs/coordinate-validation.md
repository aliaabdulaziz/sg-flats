# Block-coordinate resolution and validation

These coordinates are shared infrastructure for transport, school, food/grocery and park research. The [amenity audit](amenity-audit.md) determines which future joins are suitable; coordinate coverage alone does not validate an amenity feature.

Audit date: 5 November 2026. Read the computed counts in [onemap-summary.json](../reports/phase0/coordinates/onemap-summary.json) alongside this methodology. The output is a block-location research dataset; it does not certify PHG distance or identify an exact flat unit.

## Results

- Coordinate assignment coverage: **9,769 / 9,769 addresses**, representing all **244,230 transactions**. Assignment coverage is not a guarantee that every coordinate is independently verified.
- **1,238 addresses queried** with OneMap; 1,237 accepted through exact address/postcode and geometric corroboration rules. One queried anchor remains unresolved by OneMap but retains its separately labelled footprint match; it is not counted as officially confirmed.
- **156 / 156** stratified sample addresses agree with OneMap on postcode. All 156 use OneMap point coordinates, independently of the polygon representative-point calculation. Their prior-point offset has median **7.78 m**, maximum **53.66 m**. This is a sample consistency result, not a population error guarantee.
- **524 street codes** have at least one exact checked address, with no postcode disagreements against the earlier matches. This is anchor validation, not an API query for every address on those streets.
- Final tiers: **1,233** official-query/polygon-corroborated addresses; **4** exact OneMap addresses without a matching current polygon; **4,788** footprint-corroborated addresses; **3,744** street-crosswalk-inferred addresses. These tiers must remain visible to downstream analysis.
- Nine accepted queries use additional disambiguation: five have multiple postcode candidates but a unique matching HDB polygon; three have no postcode in the exact-address response and use a unique nearby same-block HDB polygon; one has multiple points for a unique postcode and uses its official polygon point. See `coordinate_basis` in the committed validation/evidence sample. The full 1,238-query evidence table remains local at `data/processed/onemap-validation-full.csv`.

## Method

1. Start from all 9,769 unique block/street addresses in the audited resale snapshot. Preserve transaction counts and town for coverage checks.
2. Read official HDB building polygons, retaining postcodes as strings. Project to SVY21 for geometric comparisons; quarantine four invalid polygons rather than silently repairing them.
3. Use [NUS Urban Analytics Lab's 2019 HDB dataset](https://github.com/ualsg/hdb3d-data) as a labelled footprint cross-check. Match the same block number and require a unique official footprint with intersection-over-union of at least 0.50. Do not accept globally unique block numbers alone as evidence.
4. Exclude contradictory address/object associations. Infer a street-code/name crosswalk only where at least three distinct block anchors agree and no competing street name occurs. One contradictory street code is quarantined. These inferred matches have lower assurance than direct footprint corroboration.
5. Query OneMap for unresolved addresses, a deterministic sample of three matches per confidence tier per town where available, and an anchor for every represented street code. Require exact block and canonical street agreement and a valid unique postcode. Abbreviation expansion is explicit, not fuzzy matching.
6. Compare returned OneMap points/postcodes to the original coordinates and official polygons. A postcode disagreement flags the street code for review; distant polygon disagreements are quarantined. Successful official queries replace the queried coordinates. Unqueried matches retain their original confidence label.

The deterministic NUS address holdout covered 1,263 of 1,332 held-out seed addresses and agreed on the street label in 1,262. The single disagreement exposed a Serangoon North street-code conflict, which is excluded from the combined coordinate results. This is a consistency check between related datasets, not an independent ground-truth accuracy estimate.

## Acceptance rules and limits

- Exact address comparison expands documented abbreviations such as RD/ROAD, AVE/AVENUE, CTRL/CENTRAL and ST./SAINT. It normalises apostrophes and whitespace. It never replaces a street using nearest-string similarity.
- When several exact addresses have different postcodes, accept only a unique same-block official HDB polygon candidate with a point within 100 m. This distinguishes HDB blocks from same-number private properties without selecting the first search result.
- If an exact block/street result has no postcode, accept a postcode from a unique valid same-block HDB polygon within 20 m of the returned point; label this as a spatially resolved postcode.
- When multiple points represent one exact address/postcode, a valid official polygon with the same block and postcode may supply the representative point, only if all candidate points lie within 100 m of it. Such cases are labelled with their coordinate basis; they are not independent point-distance validations.
- A point more than 100 m from its matched official polygon is a project review flag, not an official accuracy threshold.
- Full results are local at `data/processed/block_coordinates_validated.csv`. A row retains `match_status`, postcode and coordinate provenance so inferred, directly corroborated, official and unresolved results can be distinguished.
- Source OSM/NUS footprints are not survey ground truth. NUS explicitly documents association errors and shares HDB/OneMap lineage. Sample validation does not establish a guarantee for every unqueried block.
- Historical address continuity and redevelopment remain separate questions. A current geocode does not prove that an address occupied that footprint throughout 2017–2026.
- Residual ambiguous or unmatched addresses remain in review outputs with their affected transaction counts. They must not silently disappear during modelling.

## Reproduce

First run the initial download and audit commands described in [phase0-audit.md](phase0-audit.md), then:

```sh
.venv/bin/python -m pip install -r requirements-audit.txt
.venv/bin/python scripts/resolve_coordinates.py
.venv/bin/python scripts/validate_onemap.py
.venv/bin/python scripts/audit_transport_history.py
```

`resolve_coordinates.py` downloads the pinned NUS dataset if missing; its SHA-256 is recorded in the summary. The footprint-stage `summary.json` and `unresolved-addresses.csv` preserve the state before OneMap resolution; `onemap-summary.json` and `remaining-review.csv` represent the final state. The older `coordinate-candidates-unverified.csv` from the first audit remains a research artefact and is not the accepted coordinate output.

For OneMap, copy `.env.example` to a local `.env` and set `ONEMAP_ACCESS_TOKEN`. The script also supports an environment variable. Tokens and `.env` remain outside Git. The minimum successful public-address response fields are cached locally under `data/interim/`; cached results are reused. Use `--retry-unresolved` when retrying rejected queries after a matching-rule update. This flag does not refresh already accepted results. To revalidate accepted results on a later date, deliberately archive/remove the local cache first and record the new audit date.

OneMap queries use bounded pacing and retry HTTP 429 responses. A credential failure stops the script without displaying the token. The full historical LRT network and authenticated route-time filtering are outside this coordinate validation run.

OneMap API datasets are governed by the Singapore Open Data Licence according to its [API terms](https://www.onemap.gov.sg/legal/apitermsofservice.html).

See [third-party notices](third-party-notices.md) for NUS, HDB, OSM and OneMap attribution. Source and result snapshots can change; preserve the local cache and source hashes when reproducing a specific audit.
