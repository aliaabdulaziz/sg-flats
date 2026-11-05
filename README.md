# Singapore HDB Home Explorer

**Status: Broader buyer-needs and amenity audit in progress. Model training is paused pending feature-scope review. Existing transaction preparation, coordinate validation and training-only EDA are retained; no price model or app has been built.**

A reproducible project to help Singapore home seekers compare budget, space, lease, everyday amenities, schools, family proximity and workplace accessibility. Transport is one component of the housing decision. The project separates price estimation from personal location suitability and side-by-side trade-off comparison.


## The question

Given my budget, household needs and daily destinations, which HDB neighbourhoods and blocks are worth exploring—and how does an asking price compare with similar past transactions?

## Proposed experience

1. Explore historical resale transactions by budget, flat type, space, lease and location; inspect current neighbourhood profiles for schools, food/grocery access, parks and transport as sources pass audit.
2. Enter the characteristics and asking price of a specific flat; view an indicative price range and transparent comparable transactions.
3. Compare user-entered BTO assumptions with buying resale sooner or later, including optional interim housing and renovation costs.
4. Combine two independent location filters: an approximate family proximity radius and a search near a workplace or another place. Explore a public-transport commute-time option after checking routing feasibility.
5. Explore a grant guide based on household circumstances, with links to official guidance and an optional user-entered grant amount.
6. Explore future prices using adjustable scenarios; add a statistical forecast only if it outperforms simple baselines in historical testing.

The app would not establish a flat's official valuation, eligibility, available loan, cash-over-valuation, or whether it is currently for sale. HDB transactions are registered sales, not live listings. Historical transport and amenity context need dated evidence; current neighbourhood information is kept separate.

## Immediate next work

1. Audit schools, food/grocery access and parks; distinguish current explorer use from historically supported model features.
2. Extend training-only EDA and review the candidate feature set. Current dataset preparation is provisional, not the final list of buyer-relevant factors.
3. Resume a past-only comparable-sales baseline and model comparisons after the documented audit gate. Keep the final test period untouched.

## Project documents

- [Buyer needs and research questions](docs/buyer-needs.md)
- [Amenity audit, source gaps and modelling restart gate](docs/amenity-audit.md)
- [Feature audit decision register](data/reference/feature-audit-register.csv)

- [Phase 0 audit findings and reproduction steps](docs/phase0-audit.md)
- [Coordinate resolution and validation](docs/coordinate-validation.md)
- [Historical transport decisions](docs/transport-history.md)
- [Exploratory findings and hypotheses](docs/eda-findings.md)
- [Modelling dataset and evaluation design](docs/model-dataset.md)
- [Initial data dictionary](docs/data-dictionary.md)
- [Roadmap and proposed structure](docs/roadmap.md)
- [Data source research and feasibility](docs/data-sources.md)

The roadmap is a proposal; results and features are not guaranteed. Initial data snapshots were audited on 5 November 2026; the broader direction and amenity source-page review were recorded on 6 November 2026. Source metadata review is not a completed amenity ingestion audit.
