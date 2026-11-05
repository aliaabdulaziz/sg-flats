# Broader amenity and feature audit

Review date: 6 November 2026. **Status: source-page/metadata review complete for the candidates below; full-file profiling, historical reconstruction and amenity-to-block joins have not run. Model training is paused pending feature-scope review.**

This extends Phase 0 to schools, food/grocery access and parks. It does not invalidate the completed coordinate/transport work or silently add current amenities to historical records. Machine-readable decisions are in [feature-audit-register.csv](../data/reference/feature-audit-register.csv).

## Source review and immediate priorities

| Priority / source | What was verified from the official page | Decision and outstanding audit |
|---|---|---|
| P1: [MOE general school information](https://data.gov.sg/datasets/d_688b934f82c1059ed0a6993d2a829089/view) | Annual directory; displayed 2026 coverage, addresses, postcodes and school-level fields. | Candidate for named-school discovery. Fetch full file, check primary-school classification, duplicate campuses, geocoding and archived locations/closures. No historical feature approval yet. |
| P1: [NEA hawker centres collection](https://developers.data.gov.sg/datasets?resultId=1445&topics=environment) | Official location collection with a GeoJSON resource and displayed November 2025 coverage. | Resolve dataset ID from collection metadata, snapshot and profile full geometry. Opening/closure history remains unverified. Hawker centres do not cover every coffee shop or food outlet. |
| P1: [NParks parks and nature reserves](https://data.gov.sg/datasets/d_77d7ec97be83d44f61b85454f844382f/view) | Indicative polygons for NParks-managed areas, including reserves; displayed November 2025 coverage and November 2026 page update. | Candidate boundary-distance layer. Validate geometries and managed-area categories; not an entrance/accessibility map or proof all parks existed throughout 2017–2024. |
| P1: [Previously referenced supermarket dataset](https://data.gov.sg/datasets/d_cac2c32f01960a3ad7202a99c27268a0/view) | **Dataset not found** on direct official-page check. | Blocked source, not verified supermarket coverage. Locate an official replacement or assess a permitted alternative; do not substitute national annual supermarket counts for outlet locations. |
| P2: [ECDA centre listings](https://data.gov.sg/datasets/d_696c994c50745b079b3684f0e90ffc53/view) | Active-centre directory with address/postcode, operating/service information and vacancy fields. | Current discovery candidate. Full profile, freshness and licence check pending; current vacancies are neither guaranteed nor historical model inputs. |
| P2: [MOH facility finder](https://www.moh.gov.sg/seeking-healthcare/find-a-facility-or-service/types-of-medical-facilities-and-services/find-a-medical-facility/) | Official discovery starting point identified in research. | Reusable location-feed access and terms not audited. Do not claim a downloaded healthcare dataset. |

Source coverage date, page update date, first opening and geometry modification date are different. A newly refreshed page does not prove historical availability. Download/caching/redistribution terms still need recording per adopted resource.

## Audit protocol before adoption

For each candidate:

1. Resolve the exact official resource, publisher, licence/terms and access method. Record retrieval time, coverage date, version and checksum in a separate amenity source manifest; preserve existing snapshot manifests.
2. Profile full-file rows, identifiers, nulls, duplicates, category definitions and coordinate reference system. Distinguish outlets/campuses from records and geometry fragments.
3. Validate coordinates and representative sample matches geographically. Preserve ambiguous/unmatched cases; distinguish point-to-point, boundary and routed distances.
4. Investigate dated openings, relocations, closures and accessible archives. Build validity intervals where supported; do not infer dates from file-maintenance fields. Reject or constrain historical features when evidence is inadequate.
5. Calculate candidate features in projected metres with an explicit as-of policy. Publish match coverage and assumptions. Do not silently fill absent history as zero amenities.
6. Assign separate decisions for current explorer and historical price model. Publish rationale for adoption, exclusion or restricted-window use; a credible current source can still be unsuitable historically.

## Candidate feature definitions (not implemented)

| Feature group | Initial measurements | Interpretation limits |
|---|---|---|
| Schools | Approximate distance to selected primary-school locations; count of distinct primary campuses within exploratory 1 km/2 km radii | Not official home-school distance categories, admissions probability or school quality. Link to [MOE](https://p1.placement.moe.gov.sg/) and official distance tools. |
| Food/grocery | Distance to nearest verified hawker/market or supermarket; distinct venues within exploratory 500 m/1 km radii | Radius is geometric, not a walking-time claim. Opening hours, quality and affordability are not established by presence. Supermarket feed unresolved. |
| Parks | Minimum block-point-to-eligible-park-boundary distance; optionally park area within a radius | Park boundary may not be an accessible entrance. Nature reserves and small neighbourhood parks are not equivalent. |
| Transport | Existing dated MRT distance, separate from future bus/route/commute layers | Present-day footprint stability assumption persists; station age untested. |
| Personal locations | User-entered family/workplace/place filters, separately combinable | Personal suitability only; not target-side transaction characteristics or eligibility decisions. |

Thresholds are initial exploration choices, not validated natural price boundaries. Save counts and sensitivity results; avoid tuning thresholds against final test data. Do not create an opaque amenities score by arbitrarily adding incompatible distances.

## Completion gate and modelling restart

Before training resumes, deliver a source manifest for adopted downloads, full-file profiles, a temporal-use decision per priority group, and a reviewed candidate feature list. Extend training-only EDA for supported features and complete gross-price/size, outlier, recent-trend and local-comparable support checks. Record what remains current-explorer-only or unavailable.

An explicit, evidenced exclusion is a valid audit outcome. If only existing features meet historical requirements, a baseline may resume after documenting the scope decision; it must not be described as evaluating every buyer-relevant factor. Keep validation/final-test targets out of EDA and leave the current split boundaries unchanged.
