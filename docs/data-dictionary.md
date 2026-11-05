# Initial data dictionary

Based on downloaded Phase 0 snapshots. Names below are source fields or explicitly proposed derived fields; their presence does not imply a model has been trained.

## Resale transactions

| Field | Interpretation | Use / caveat |
|---|---|---|
| `month` | Registration month, YYYY-MM | Chronological splits and trends; no exact transaction day. Current month is incomplete. |
| `town` | HDB town label | Categorical location; not interchangeable with other agencies' planning-area definitions. |
| `flat_type` | Flat category | Preserve rare categories and inspect before deciding scope. |
| `block`, `street_name` | Block/street address | Join to property file; no unit number or postcode. |
| `storey_range` | E.g. `10 TO 12` | Parse lower/upper bounds; midpoint is an approximation. |
| `floor_area_sqm` | Source floor area in sqm | Positive numeric; unusual models can have large values. |
| `flat_model` | Model label, e.g. Improved or Terrace | Categorical; distinguish model-specific differences. |
| `lease_commence_date` | Lease commencement year | Integer year despite field name; not exact building completion date. |
| `remaining_lease` | Source years/months remaining at resale application | Parse to months; use for historic record, age forward for scenarios separately. |
| `resale_price` | Registered resale price in S$ | Proposed target, not an asking price or official valuation. |

No transaction ID is supplied. Fully identical records may represent separate transactions.

## HDB property information

| Field/group | Interpretation | Use / caveat |
|---|---|---|
| `blk_no`, `street` | Block/street | Unique composite key in audited snapshot. |
| `max_floor_lvl`, `year_completed` | Building-level floor and completion fields | Numeric conversion and historical validity need checking before use. |
| `residential`, `commercial`, `market_hawker`, `miscellaneous`, `multistorey_carpark`, `precinct_pavilion` | Building flags | Current-snapshot attributes, not proven historic features. |
| `bldg_contract_town` | HDB building contract town code | Not the same representation as transaction `town`. |
| `total_dwelling_units`, room-type sold/rental count columns | Building unit counts | Snapshot counts; do not assume historic values. |

## HDB building GeoJSON

| Field | Interpretation | Use / caveat |
|---|---|---|
| `BLK_NO`, `ST_COD` | Block and street code | Composite address key; street-name bridge unresolved. |
| `POSTAL_COD` | Postal code | Keep as string to preserve leading zeroes. |
| `OBJECTID`, `ENTITYID`, `INC_CRC` | Source identifiers/checksum-like attributes | Do not treat as transaction identifiers. |
| `FMEL_UPD_D` | Source update field | Not an opening or completion date. |
| `SHAPE.AREA`, `SHAPE.LEN` | Source geometry measures | Not flat floor area. |
| `geometry` | Polygon/MultiPolygon coordinates | Inspect CRS and choose a justified building representative point before distances. |

## LTA transport files

- Station polygons: `STN_NAM` is frequently a code, not a human-readable name; `LIN_NAM` is a source line code. Repeated station labels and nonstandard labels need review. `TYP_CD` must be interpreted with a codebook.
- Station exits: `stn_name`, `exit_code` and Point geometry; current snapshot with no audited opening dates.
- Bus stops: `BUS_STOP_N` (string stop code), `LOC_DESC`, `STATUS`, `SERVICE_TY`, and Point geometry. Stop codes repeat for six rows; investigate before deduplication.
- Road sections (investigated alternative): `RD_CD` and line geometry, but no road-name attribute in the download. Cannot directly bridge building street codes to names.
- `.prj` files identify projected SVY21 in metres. Metadata creation/update fields are not service-start dates.

## Proposed derived fields

- `address_key`: uppercase, trim and collapse whitespace, then join block and street with `|`. No fuzzy matching in the audit.
- `remaining_lease_months`: years × 12 plus months, preserving the source string.
- `storey_lower`, `storey_upper`: parsed bounds from `storey_range`.
- `price_per_sqm`: price divided by area for analysis only; cannot be an input to a model predicting that same price.
- Future distance/commute fields: not yet generated; require verified block coordinates and an explicit infrastructure date and route assumption.

## Generated coordinate and historical transport outputs

- `block_coordinates_validated.csv` (local): one row per transaction address, preserving `address_key`, transaction count, town, postcode, coordinates and `match_status`. Confidence tiers distinguish `footprint_corroborated`, `street_crosswalk_inferred`, `onemap_exact_polygon_corroborated` and `onemap_exact_no_polygon`; official evidence additionally records `coordinate_basis` for disambiguation.
- `mrt_station_proxies.csv` (local): one row per registered MRT service code with a station-area representative point and geometry method. Interchange codes may share a physical-station proxy.
- `rail-service-register.csv`: source-linked service availability, date type and history scope. A 2017-01-01 left-censored boundary is not an opening date. Announced future dates are separate from verified availability.
- `monthly-availability-policy.csv`: services opening during a transaction month become available from the next full month for historical features.

## Prepared modelling records

See [modelling dataset and evaluation design](model-dataset.md) for the target, feature definitions, QA fields and split policy, and [feature allowlist](../config/model-data.json) for exact model input names. Generated transaction records remain local; coverage and lineage are in `reports/model-data/`.

## Planned broader features (not generated)

The current schema covers transaction attributes and conditional MRT distances; it is provisional. School proximity, food/grocery access and park-boundary distance/count measures are candidates in [amenity-audit.md](amenity-audit.md), with status in [feature-audit-register.csv](../data/reference/feature-audit-register.csv). They are not columns in the current prepared dataset. Preserve source date, validity interval, geometry method and missingness for any future adopted feature. Personal family/workplace inputs and unobserved unit condition are not transaction-model fields.
