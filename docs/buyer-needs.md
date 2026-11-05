# Buyer needs and research questions

Direction agreed 6 November 2026. The project helps buyers compare homes against budget and daily-life needs. MRT access is one candidate factor, alongside amenities, schools, space, lease, family and workplace access. It is not an MRT-premium study.

## Three product questions

1. **What might this flat reasonably cost?** Estimate recorded gross resale price from available characteristics and compare with relevant past transactions. Explain missing condition/layout information and measured prediction errors.
2. **Would this location suit my household?** Explore named schools, daily food/grocery access, green space and transport; combine independent family and workplace/place filters.
3. **What trade-offs am I making?** Compare shortlisted blocks by indicative price, space, lease and amenity access. Avoid a universal best-neighbourhood score: households value these differently.

## Qualitative evidence

This is a targeted desk review, not interviews, a representative survey, a systematic review or a measured ranking of buyer priorities. Forum comments are self-selected anecdotes; property-editorial claims are hypotheses, not proof of price effects. Do not turn opinions into guaranteed appreciation, eligibility rules or numerical model coefficients.

| Source | Themes informing requirements | Limit |
|---|---|---|
| [Resale purchase experiences, r/askSingapore](https://www.reddit.com/r/askSingapore/comments/18w7qj3/share_your_resale_flat_purchase_experience/) | Family proximity, daily amenities, privacy, floor preferences, renovation and neighbours | Older anecdotal discussion; individual needs differ. |
| [What to look out for when purchasing resale, r/askSingapore](https://www.reddit.com/r/askSingapore/comments/1uuhljw/what_to_look_out_for_when_purchasing_resale/) | Afternoon sun, hidden defects, neighbours, noise, layout and transport trade-offs | Personal accounts, not verified technical or financial advice. |
| [PropertyGuru resale buying guide](https://www.propertyguru.com.sg/property-guides/resale-hdb-flat-what-to-consider-43089) | Convenience/noise trade-off, wear and tear, lease and total purchase considerations | Article updated February 2021; do not use its financial figures as current policy. |
| [99.co resale guide](https://www.99.co/singapore/hdb-resale-price) | Size, floor, lease, condition, schools and retail amenities alongside rail | Commercial editorial; numerical premium claims are not adopted. |

## Requirements and boundaries

| Need | First implementation direction | Role |
|---|---|---|
| Affordability and value | Gross price estimate, past comparables, user-entered renovation/cost assumptions | Model plus planning view; grants/finance remain separate |
| Space, floor, lease and layout | Existing type/area/model/storey/lease fields; viewing checklist for actual layout | Model candidates and filters; flat model is only a layout proxy |
| School access | Named-school search and clearly labelled approximate proximity | Current explorer first; historical model only after location/date audit |
| Daily convenience | Hawker/market, supermarket and park profiles | Current explorer plus candidate historical features |
| Family and workplace | Independent, combinable address-radius filters; commute estimates after routing tests | Personal preference, not household attributes added to transaction model |
| Comfort and condition | Viewing checklist for sun, ventilation, noise, privacy, defects and renovation | Not observed in resale records; block coordinates cannot establish unit conditions |
| Other household services | Childcare and healthcare discovery after core amenities | Later current-context layers; presence does not establish vacancies or service quality |

Do not label schools good/bad or infer neighbourhood quality from demographic stereotypes. Do not infer bedroom count from HDB room labels. Keep school admissions, PHG and financing assessments with official services.

## Broader exploratory hypotheses

These extend, rather than replace, the initial EDA register. They are not findings yet.

| ID | Question / hypothesis | Planned analysis and boundary |
|---|---|---|
| B1 | Food/grocery accessibility provides price information beyond town, coordinates and flat characteristics. | Distance and choice-count features; compare otherwise supported groups and identical validation rows. History required. |
| B2 | School proximity relates to prices and matters differently to households. | Named schools and school-level categories; no invented quality ranking or admissions guarantee. Check relocations/closures. |
| B3 | Green-space proximity relates to prices and improves household choice. | Park-boundary distance as a clearly labelled geometric proxy; access routes and entrances can differ. |
| B4 | Some apparent MRT association reflects other neighbourhood amenities. | Add eligible amenity groups before attributing incremental value to MRT; sequential and leave-one-group-out model comparisons. No causal premium claim. |
| B5 | Larger flats cost more in total, while price per square metre can behave differently. | Gross-price and S$/m² plots within common types, lease bands and years; avoid denominator-based misinterpretation. |
| B6 | Lease, floor and flat-model relationships vary by location and transaction time. | Training-only distributions, interactions and support checks; validate any selected transformations. |
| B7 | The best shortlist depends on household preferences, not price alone. | Explain side-by-side trade-offs and user-selected requirements; qualitative evidence supports design, not a validated satisfaction model. |

## Immediate sequence

1. Complete the broader source and feature audit in [amenity-audit.md](amenity-audit.md).
2. Extend training-only EDA where historically defensible features exist; complete gross-price, unusual-record, recent-trend and local-support checks with existing fields.
3. Record include/exclude decisions, feature definitions and baseline acceptance criteria before model selection. Historical gaps can lead to explicit current-explorer-only decisions; they do not need to block every future model indefinitely.
4. Resume baseline development after this review, preserve chronological splits, then compare base, amenity and transport feature groups on the same development windows.

No new buyer interviews, amenity acquisition, price model or app is claimed to have been completed by this desk review.
