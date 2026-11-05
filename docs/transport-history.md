# Transport history: what can be used safely

Reviewed 5 November 2026. The executable audit is `scripts/audit_transport_history.py`; its sourced service-date register is [rail-service-register.csv](../data/reference/rail-service-register.csv). Computed checks are in [transport/summary.json](../reports/phase0/transport/summary.json).

## Decision

| Data / feature | Current explorer | Historical price model |
|---|---|---|
| MRT service-code availability | Use the verified service dates and exclude future/deferred services | Supported for the registered MRT set from 2017, subject to the month policy below. |
| Approximate distance to physical MRT station | Use an explicitly labelled station-area point | Conditional: combine dated service availability with the documented assumption that the current earliest-service station footprint is a reasonable proxy for the station's historical location. It is not an audited historical entrance point. |
| Distance to a station exit | Useful current-snapshot feature | Excluded until exit-specific opening/relocation dates are established. Station opening does not prove every present-day exit existed then. |
| Bus-stop proximity, service counts and routes | Useful after verifying service codes and current API access | Excluded: snapshot update/creation fields are not reliable evidence of historical service availability or stop relocation. |
| LRT network proximity | Keep distinct from MRT and verify current operational status | Excluded from the initial historical model: a complete station-level timeline is not yet audited. Teck Lee's opening is recorded as an event only. |
| OneMap commute estimate | A planning estimate for the requested date/time, after routing tests | Excluded from historical modelling: no verified reconstruction of past timetables, routes or walking networks. |

## MRT register and geometry

The LTA code/name workbook contains 213 service-code rows, including LRT and some services whose operational status must be established separately. A name in that workbook is not proof a service was operating on the workbook's date. The registry adds sourced later openings and explicitly excludes announced future or deferred services.

For the current audit, the registry supports 174 MRT service-code rows corresponding to 146 physical station names. Six codes lack an exact polygon label: NE1, TE9, TE11, TE14, TE17 and TE20. They are resolved using the official shared station-name crosswalk to a polygon for an existing service at the interchange. Repeated polygons are combined. Station names are whitespace-normalised; this prevents a trailing-space variant of Woodlands being treated as a separate station.

The generated local `data/processed/mrt_station_proxies.csv` has a point for each registered MRT service code. A representative point is calculated inside the union of the current footprints associated with the physical station's earliest registered service, avoiding the inclusion of a later line's footprint where an older one is available. This is a coarse station-location proxy. Its source is current geometry; historical footprint stability remains an explicit assumption to test, not an established fact.

## Month-level policy

HDB transactions have a registration month, not a day. A station opening mid-month cannot safely be assigned to every transaction in that month. The register therefore makes a newly opened service available from the **following full month** for historical features. Ten regression cases cover dates before, during and after selected openings.

For MRT services already operating before January 2017, `available_from=2017-01-01` is a left-censored modelling-window boundary, **not the actual station-opening date**. The source history establishes earlier line stages; this register is not intended for transactions before 2017. First full service month is January 2017 for those rows.

Registration timing also differs from when a buyer agreed a price. A later analysis should test lagged access features. Announced future transport can influence prices, but any anticipation feature needs its own dated announcement information; it must not be labelled as operational access.

## Sourced changes in the modelling window

- Tuas West Extension: passenger service on 18 June 2017. [MOT opening speech](https://www.mot.gov.sg/news-resources/newsroom/speech-by-second-minister-ng-chee-meng-at-tuas-west-extension-opening-ceremony/).
- Downtown Line Stage 3: 21 October 2017; Hume: 28 February 2025. [LTA DTL history](https://www.lta.gov.sg/content/ltagov/en/getting_around/public_transport/rail_network/downtown_line.html).
- Canberra: 2 November 2019. [LTA 2019/20 report](https://www.lta.gov.sg/content/dam/ltagov/who_we_are/statistics_and_publications/report/pdf/LTA_AR1920.pdf).
- TEL phases: 31 January 2020, 28 August 2021, 13 November 2022 and 23 June 2024. Deferred stations are not assigned the opening of their surrounding stage. [LTA TEL history](https://www.lta.gov.sg/content/ltagov/en/upcoming_projects/rail_expansion/thomson_east_coast_line.html).
- Punggol Coast: 10 December 2024. [LTA opening factsheet](https://www.lta.gov.sg/content/ltagov/en/newsroom/2024/12/news-releases/punggol_coast_station_welcomes_commuters.html).
- Circle Line Stage 6: 12 July 2026. [LTA CCL6](https://www.lta.gov.sg/content/ltagov/en/upcoming_projects/rail_expansion/circle_line_6.html).
- TEL5/DTL3 extension has an announced 26 December 2026 date and remains excluded as of this audit. [LTA announcement](https://www.lta.gov.sg/content/ltagov/en/newsroom/2026/11/news-releases/tel5-dtl3e-passenger-service-26-dec-2026.html).

LRT illustrates why a blanket line-opening date is unsafe: [Teck Lee opened on 15 August 2024](https://www.lta.gov.sg/content/ltagov/en/newsroom/2024/7/news-releases/Teck_Lee_LRT_station_to_start_operations.html), while [Ten Mile Junction's service ended from 13 January 2019](https://www.lta.gov.sg/content/dam/ltagov/news/press/2018/20181212_BPLRT_train_timings_AnnexA.pdf). Current snapshots cannot represent that entire history.

## Remaining limits

This audit is a service-opening register, not a complete record of temporary closures, disruptions, timetable changes, accessible entrances or walk routes. Before modelling, compare a baseline without transport against date-filtered station-proxy features and test sensitivity to registration lags and location uncertainty. Keep current-map conveniences separate from historical model inputs.
