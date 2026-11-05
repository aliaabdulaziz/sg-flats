"""Training-only descriptive EDA. Run after scripts/prepare_model_data.py."""
import hashlib
import html
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/eda'


def chart(frame, label, value, filename, title, unit, note):
    """Standalone, accessible horizontal bar chart of a small aggregate table."""
    width, left, right, row = 1000, 210, 150, 34
    height = 130 + row * len(frame)
    maximum = float(frame[value].max()) * 1.05
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
             f'<title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(note)}</desc>',
             '<rect width="100%" height="100%" fill="#ffffff"/>',
             '<g font-family="Arial, sans-serif" fill="#16324f">',
             f'<text x="24" y="32" font-size="21" font-weight="bold">{html.escape(title)}</text>',
             f'<text x="24" y="57" font-size="13">{html.escape(unit)}</text>']
    for i, (_, r) in enumerate(frame.iterrows()):
        y = 78 + i * row
        w = float(r[value]) / maximum * (width - left - right)
        parts.extend([f'<text x="{left-12}" y="{y+18}" text-anchor="end" font-size="13">{html.escape(str(r[label]))}</text>',
                      f'<rect x="{left}" y="{y}" width="{w:.2f}" height="24" rx="3" fill="#267f85"/>',
                      f'<text x="{left+w+9:.2f}" y="{y+18}" font-size="13">{float(r[value]):,.0f}</text>'])
    parts.extend([f'<text x="24" y="{height-18}" font-size="12">{html.escape(note)}</text>', '</g></svg>'])
    (OUT / 'figures' / filename).write_text('\n'.join(parts) + '\n')


def summarise(df, keys):
    return df.groupby(keys, observed=True).agg(
        transactions=('resale_price', 'size'), addresses=('address_key', 'nunique'),
        median_price=('resale_price', 'median'), median_psm=('price_psm', 'median'),
        median_area=('floor_area_sqm', 'median'), median_lease_years=('lease_years', 'median')
    ).reset_index()


def main():
    source = ROOT / 'data/processed/model-transactions.csv'
    config = json.loads((ROOT / 'config/model-data.json').read_text())
    # Filtering precedes any exploratory price calculation.
    df = pd.read_csv(source).loc[lambda x: x.split.eq('train')].copy()
    start, end = config['splits']['train']
    if df.empty or not df.month.between(start, end).all():
        raise ValueError('Training membership inconsistent with configuration')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'figures').mkdir(exist_ok=True)
    df['year'] = df.month.str[:4].astype(int)
    df['price_psm'] = df.resale_price / df.floor_area_sqm
    df['lease_years'] = df.remaining_lease_months / 12
    df['mrt_band'] = pd.cut(df.nearest_mrt_distance_m, [-np.inf, 500, 1000, 1500, np.inf],
                             labels=['0–500 m', '500–1,000 m', '1,000–1,500 m', 'Over 1,500 m'])
    df['lease_band'] = pd.cut(df.lease_years, [0, 50, 60, 70, 80, 90, 100], right=False)
    df['area_band'] = (df.floor_area_sqm // 10).astype(int)
    tables = {}
    for name, keys in [('annual', ['year']), ('town', ['town']), ('flat-type', ['flat_type']),
                       ('lease', ['lease_band']), ('mrt-distance', ['mrt_band']),
                       ('town-year', ['town', 'year']), ('type-year', ['flat_type', 'year']),
                       ('coordinate-confidence', ['match_status'])]:
        tables[name] = summarise(df, keys)
        tables[name].to_csv(OUT / f'{name}.csv', index=False, float_format='%.6f')
    numeric = ['resale_price', 'price_psm', 'floor_area_sqm', 'lease_years',
               'storey_lower', 'month_index', 'nearest_mrt_distance_m']
    # Spearman correlation: ranks, then Pearson; avoids an additional scipy dependency.
    df[numeric].rank().corr().to_csv(OUT / 'spearman-correlations.csv')
    # Compare the same town/type cells across every year, retaining fixed 2017 weights.
    cells = df.groupby(['town', 'flat_type', 'year']).resale_price.agg(['size', 'median']).reset_index()
    valid = cells.loc[cells['size'] >= 30].groupby(['town', 'flat_type']).year.nunique()
    common_cells = valid[valid == df.year.nunique()].reset_index()[['town', 'flat_type']]
    cells = cells.merge(common_cells, on=['town', 'flat_type'], validate='many_to_one')
    weights = cells.loc[cells.year.eq(2017), ['town', 'flat_type', 'size']].rename(columns={'size': 'weight'})
    cells = cells.merge(weights, on=['town', 'flat_type'], validate='many_to_one')
    cells['weighted_price'] = cells['median'] * cells.weight
    adjusted = cells.groupby('year').agg(numerator=('weighted_price', 'sum'), denominator=('weight', 'sum'))
    adjusted['fixed_mix_cell_median_average'] = adjusted.numerator / adjusted.denominator
    adjusted = adjusted.reset_index()
    adjusted.to_csv(OUT / 'fixed-mix-trend.csv', index=False, float_format='%.6f')
    # Close vs far comparisons, progressively restricting comparability. No causal interpretation.
    comparisons = []
    strata_tables = []
    df['distance_group'] = np.where(df.nearest_mrt_distance_m <= 500, 'near',
                                    np.where(df.nearest_mrt_distance_m > 1000, 'far', 'middle'))
    selected = df.loc[df.distance_group.ne('middle')]
    for name, keys in [('town_type_year', ['town', 'flat_type', 'year']),
                       ('plus_area_lease', ['town', 'flat_type', 'year', 'area_band', 'lease_band'])]:
        grouped = selected.groupby(keys + ['distance_group'], observed=True).price_psm.agg(['size', 'median'])
        paired = grouped.unstack('distance_group').dropna()
        paired = paired.loc[(paired['size']['near'] >= 20) & (paired['size']['far'] >= 20)]
        weight = paired['size']['near'] + paired['size']['far']
        gap = 100 * (paired['median']['near'] / paired['median']['far'] - 1)
        comparisons.append({'comparison': name, 'eligible_strata': len(paired),
                            'represented_rows': int(weight.sum()),
                            'weighted_mean_within_stratum_gap_pct': float(np.average(gap, weights=weight)),
                            'median_stratum_gap_pct': float(gap.median()),
                            'share_positive_strata': float((gap > 0).mean())})
        detail = paired.copy(); detail.columns = ['_'.join(c) for c in detail.columns]
        detail['near_vs_far_gap_pct'] = gap
        detail.reset_index().to_csv(OUT / f'mrt-strata-{name}.csv', index=False, float_format='%.6f')
    pd.DataFrame(comparisons).to_csv(OUT / 'mrt-stratified-comparison.csv', index=False, float_format='%.6f')
    # Within-town/type/year correlations reduce some composition differences, not all confounding.
    correlations = []
    for key, group in df.groupby(['town', 'flat_type', 'year']):
        if len(group) < 30:
            continue
        for feature in ['lease_years', 'storey_lower', 'floor_area_sqm']:
            value = group[[feature, 'price_psm']].rank().corr().iloc[0, 1]
            if pd.notna(value):
                correlations.append({'town': key[0], 'flat_type': key[1], 'year': key[2],
                                     'feature': feature, 'transactions': len(group), 'spearman': value})
    corr = pd.DataFrame(correlations)
    corr.to_csv(OUT / 'within-group-correlations.csv', index=False, float_format='%.6f')
    corr_summary = corr.groupby('feature').agg(strata=('spearman', 'size'),
        median_spearman=('spearman', 'median'),
        share_positive=('spearman', lambda x: (x > 0).mean())).reset_index()
    corr_summary.to_csv(OUT / 'within-group-correlation-summary.csv', index=False, float_format='%.6f')
    rare = tables['flat-type'][['flat_type', 'transactions']].to_dict('records')
    lag_change = (df.nearest_mrt_distance_m - df.nearest_mrt_distance_lag1_m).abs()
    chart(tables['annual'], 'year', 'median_price', 'annual-price.svg',
          'Annual median resale price', 'Singapore dollars · training period 2017–2024',
          'Unadjusted transaction medians; changes in flat mix can affect the trend.')
    chart(tables['flat-type'].sort_values('transactions'), 'flat_type', 'transactions', 'flat-type-support.svg',
          'Transaction coverage by flat type', 'Number of transactions · training period 2017–2024',
          'Rare categories need separate error reporting; counts do not establish accuracy.')
    chart(tables['mrt-distance'], 'mrt_band', 'median_psm', 'mrt-price.svg',
          'MRT proximity and median price per square metre', 'S$ per square metre · training period 2017–2024',
          'Unadjusted association; station-point straight-line distance, not walking distance.')
    chart(tables['lease'].assign(label=lambda x: x.lease_band.astype(str)), 'label', 'median_psm',
          'lease-price.svg', 'Remaining lease and median price per square metre',
          'S$ per square metre · lease bands in years · training period 2017–2024',
          'Pooled comparison; town, transaction year, flat type and location also differ.')
    chart(tables['town'].sort_values('median_psm'), 'town', 'median_psm', 'town-price.svg',
          'Median resale price per square metre by town', 'S$ per square metre · training period 2017–2024',
          'Pooled medians; differences are not estimates of a town effect.')
    summary = {'training_months': [df.month.min(), df.month.max()], 'training_rows': len(df),
               'training_addresses': int(df.address_key.nunique()),
               'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
               'analysis_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'other_splits_analysed': False, 'annual': tables['annual'].to_dict('records'),
               'fixed_mix_cells': len(common_cells), 'fixed_mix_training_rows': int(cells['size'].sum()),
               'fixed_mix': adjusted.to_dict('records'), 'mrt_comparisons': comparisons,
               'within_group_correlations': corr_summary.to_dict('records'),
               'flat_type_support': rare, 'lag1_distance_changed_rows': int((lag_change > 0.01).sum()),
               'station_age_hypothesis': 'NOT TESTED: verified pre-2017 opening dates unavailable',
               'causal_effects_estimated': False}
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
