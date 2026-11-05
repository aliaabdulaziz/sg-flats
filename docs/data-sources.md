# Data source research

Research date: 5 November 2026. The initial source review is now supplemented by a [downloaded-data audit](phase0-audit.md). HDB resale, property and building data and LTA static transport files were downloaded and profiled. [Coordinate matching and sampled OneMap validation](coordinate-validation.md) have now been run; [transport history](transport-history.md) is assessed separately. Full historical network reconstruction and route-time API testing remain unverified. Check current terms before acquisition, redistribution or deployment.

This is a research inventory, not a list of datasets already used. The proposed core sources below are starting points for the data audit; the remaining sources are optional references or alternatives. We will record which sources are actually adopted after testing coverage, matching and usage terms.

## Audit status

- Downloaded and profiled: HDB 2017-onward resale, Property Information, Existing Building, LTA station polygons, station exits and bus-stop points.
- Investigated alternative: LTA Road Section Line; no road-name field was present, so it did not solve the building street-code bridge.
- OneMap authenticated address search: tested using a locally configured token. No token is committed. LTA dynamic routes/services and OneMap route-time performance remain untested.
- NUS Urban Analytics Lab hdb3d-data: adopted as a labelled footprint corroboration source, with pinned version and known-error caveats; see [attribution](third-party-notices.md).
- LTA station-code workbook and official LTA/MOT opening announcements: used to build the sourced MRT service register.
- Additional source candidates remain research only unless identified in the audit. Download success does not imply a source is approved for historical model features.

## Proposed core sources

| Source | What it can contribute | Access and limitations |
|---|---|---|
| [HDB resale flat prices, 2017 onward](https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view) | Registered transaction month, block/street, flat type, floor area, storey range, lease and price. | CSV/API, Singapore Open Data Licence as stated on the dataset. Not current listings or official valuation; condition and exact unit floor are not supplied. |
| [HDB Property Information](https://data.gov.sg/datasets?agencies=HDB&resultId=d_17f5382f26140b1fdae0ba2ef6239d2f) | Block and street, completion year, maximum floor and some building-level characteristics. | CSV; dataset notes no postal-code information. Test address matching and time consistency. |
| [OneMap Search API](https://www.onemap.gov.sg/apidocs/search) | Geocode HDB addresses and points of interest to coordinates. | Token authentication required. Check matching quality, rate limits, permitted caching and display terms. Search results need validation. |
| [LTA DataMall static datasets](https://datamall.lta.gov.sg/content/datamall/en/static-data.html) | Train station and station exit locations and station codes; other geospatial layers. | File availability and join fields need verification. Current location does not show opening date; confirm historical network separately. |
| [LTA DataMall dynamic datasets](https://datamall.lta.gov.sg/content/datamall/en/dynamic-data.html) | Current bus-stop coordinates and bus routes/services. | API access registration; [LTA API terms](https://datamall.lta.gov.sg/content/datamall/en/api-terms-of-service.html) apply. Current routes and stops are not proof of past availability or useful commute times. |

## Additional sources researched

These are potential alternatives or later additions; they are not commitments to use them.

| Source | What it can contribute | Access and limitations |
|---|---|---|
| [Older HDB resale price datasets](https://data.gov.sg/datasets?query=resale%20flat%20prices) | Longer history for analysis or forecasting. | Multiple periods and differing definitions (approval vs registration date); check schema and comparability. |
| [HDB Existing Building](https://data.gov.sg/datasets?query=bto&resultId=d_16b157c52ed637edd6ba1232e026258d) | Geographic building polygons, block number and postal code may assist block geolocation. | GeoJSON snapshot; linking via street codes and postal code needs investigation. Current buildings do not guarantee historic coverage. |
| [HDB resale statistics and index](https://www.hdb.gov.sg/managing-my-home/selling-a-flat/process-for-selling-a-flat/resale-flat-planning/resale-statistics) | Market-level context and long-run quarterly index; official town/type medians. | Market-wide index is not an individual-flat forecast. Sparse town/type quarters need caution. |
| [HDB BTO launch annexes](https://www.hdb.gov.sg/-/media/hdb-pulse/news/2026/20260617-HDB-Launches-6952-Flats-Across-7-Projects-in-June-2026-BTO-Sales-Exercise/Annex-A.pdf) | Project prices, location, attributes and nearby resale comparisons for a launch. | PDF example; check launch-by-launch structure and reuse. Price ranges are not guaranteed individual unit prices. Start with user-entered assumptions. |
| [MOE school information](https://developers.data.gov.sg/datasets?agencies=Ministry+of+Education+%28MOE%29&resultId=d_688b934f82c1059ed0a6993d2a829089) | School addresses for a potential later amenities layer. | Geocode and check currency and historical coverage. Distance alone does not establish admissions eligibility. |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) | Potential supplementary map and geographic data. | Check quality and coverage; ODbL attribution and applicable share-alike obligations. Map tiles have separate usage policies. |

| [OneMap routing API](https://www.onemap.gov.sg/apidocs/routing) | Potential walking and public-transport journey estimates to a user-selected destination. | Requires authentication; check quotas, terms, performance and coverage. Test date/time support and clarify estimates are not guarantees. |
| [HDB rental data from 2021](https://data.gov.sg/datasets/d_c9f57187485a850908655db0e8cfe651/view) | Historical rental context for interim housing scenarios. | Updated historical records, not live listings; rents are owner-declared and HDB does not verify their accuracy. |
| [OneMap thematic layers](https://www.onemap.gov.sg/apidocs/) | Potential amenity information for later exploration. | Check layer-specific coverage, currency, access and terms. |
| [LTA bus arrival API](https://datamall.lta.gov.sg/content/datamall/en/dynamic-data.html) | Real-time arrival estimates for services at a selected stop. | Requires DataMall account key; lower priority than routes and useful journey options. |

## Official grant guidance

- [HDB PHG distance enquiry](https://www.hdb.gov.sg/check-distance-for-proximity-housing-grant/get-help): official check for the proximity condition. An app-drawn radius is approximate and is not confirmation of eligibility.
- [HDB PHG for singles](https://www.hdb.gov.sg/buying-a-flat/flat-grant-and-loan-eligibility/singles/proximity-housing-grant) and [for families](https://www.hdb.gov.sg/buying-a-flat/flat-grant-and-loan-eligibility/couples-and-families/proximity-housing-grant): current conditions for the grant; verify the relevant household and property conditions.
- [HDB Flat Eligibility letter](https://www.hdb.gov.sg/buying-a-flat/flat-grant-and-loan-eligibility/application-for-an-hdb-flat-eligibility-hfe-letter): official assessment route. Grant guidance in the app should be reviewed and dated as policy changes.

## Property websites

Use real estate sites for market context and descriptions of buyer problems, and trace numeric claims to their stated original source where possible. For instance, HDB itself publishes BTO launch comparisons and transaction prices. PropertyGuru's [agent content guidelines](https://www.agentofferings.propertyguru.com.sg/help-centre/manage-your-listings/listing-guidelines-and-policies/advertisement-and-content-guidelines-propertyguru-singapore/) prohibit unauthorised automated collection for the agent service; check applicable site terms, obtain permission or use a licensed feed before collecting or republishing listings. Do not assume a public page is open data. Live listings are not required for the initial release.

## Open questions before modelling

- Can addresses be matched to a block coordinate accurately and consistently? Test samples, ambiguous addresses and unmatched rates.
- Are station opening dates and historical bus stops/routes available in a reusable, reliable form? If not, omit or constrain historical features to prevent future information leaking into training.
- How recent and complete are comparable sales for each area and flat type? Show sample counts and avoid confident estimates in sparse areas.
- Can a realistic, evaluated interval be produced for individual flat prices? Check coverage on later data, and do not confuse assumptions with confidence.
- Is there sufficient stable historical data to backtest a four-year forecast? Keep scenarios explicitly hypothetical unless evidence supports more.
