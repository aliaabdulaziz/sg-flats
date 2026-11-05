"""Prepare snapshot-specific modelling records; no fitting or test-score inspection."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    config_path = ROOT / 'config/model-data.json'
    config = json.loads(config_path.read_text())
    inputs = [ROOT / p for p in [
        'data/raw/resale.csv', 'data/processed/block_coordinates_validated.csv',
        'data/processed/mrt_station_proxies.csv',
        'reports/phase0/transport/monthly-availability-policy.csv',
        'config/model-data.json']]
    lineage = {str(p.relative_to(ROOT)): digest(p) for p in inputs}
    df = pd.read_csv(inputs[0], dtype={'block': str})
    raw_columns = list(df.columns)
    source_hash = lineage['data/raw/resale.csv']
    df['record_id'] = [hashlib.sha256(f'{source_hash}:{i}'.encode()).hexdigest()
                       for i in range(1, len(df) + 1)]
    df['repeated_source_row'] = df.duplicated(raw_columns, keep=False)
    norm = lambda s: s.str.upper().str.strip().str.replace(r'\s+', ' ', regex=True)
    df['address_key'] = norm(df.block) + '|' + norm(df.street_name)
    coords = pd.read_csv(inputs[1], dtype={'postcode': str})
    require(coords.address_key.is_unique, 'Coordinate address keys must be unique')
    df = df.merge(coords[['address_key', 'postcode', 'match_status', 'x_svy21', 'y_svy21']],
                  on='address_key', how='left', validate='many_to_one')
    require(len(df) == len(pd.read_csv(inputs[0])), 'Join changed transaction count')
    require(df[['x_svy21', 'y_svy21', 'postcode']].notna().all().all(), 'Missing coordinates')
    lease = df.remaining_lease.str.extract(r'^(\d+) years?(?: (\d+) months?)?$')
    require(lease[0].notna().all(), 'Unrecognised remaining lease')
    df['remaining_lease_months'] = lease[0].astype(int) * 12 + lease[1].fillna(0).astype(int)
    storey = df.storey_range.str.extract(r'^(\d+) TO (\d+)$').astype(int)
    df['storey_lower'], df['storey_upper'] = storey[0], storey[1]
    require((df.storey_lower <= df.storey_upper).all(), 'Invalid storey range')
    months = pd.to_datetime(df.month, format='%Y-%m', errors='raise')
    df['month_index'] = (months.dt.year - 2017) * 12 + months.dt.month - 1
    df['split'] = 'excluded_incomplete_month'
    previous_end = ''
    for name, (start, end) in config['splits'].items():
        require(start <= end and start > previous_end, 'Overlapping or unordered splits')
        mask = df.month.between(start, end)
        require(mask.any(), f'Empty split: {name}')
        df.loc[mask, 'split'] = name
        previous_end = end
    cutoff = config['snapshot_as_of'][:7]
    require(previous_end < cutoff, 'Final split includes snapshot month')
    require(df.loc[df.split.str.startswith('excluded'), 'month'].eq(cutoff).all(),
            'Unexpected excluded historical month; review split configuration')
    policy = pd.read_csv(inputs[3])
    points = pd.read_csv(inputs[2])
    require(policy.station_code.is_unique and points.station_code.is_unique, 'Duplicate MRT code')
    stations = policy.merge(points, on=['station_code', 'station_name'], validate='one_to_one')
    require(len(stations) == len(policy), 'Missing station proxy')
    # Codes at an interchange share one physical-station proxy. Date availability is checked per month.
    for lag, suffix in [(0, ''), (1, '_lag1')]:
        distance_col = f'nearest_mrt_distance{suffix}_m'
        df[distance_col] = np.nan
        if lag == 0:
            df['nearest_mrt_station'] = ''
        for month, indices in df.groupby('month', sort=True).groups.items():
            as_of = str(pd.Period(month, freq='M') - lag)
            # Legacy network is left-censored at 2017-01; Dec 2016 lag uses that same known baseline.
            active = stations.loc[(stations.first_full_service_month <= as_of) |
                ((as_of < '2017-01') & stations.date_type.eq('left_censored_before_model_window'))]
            active = active.drop_duplicates('station_name').reset_index(drop=True)
            require(len(active) > 0, 'No active MRT stations')
            a = df.loc[indices, ['x_svy21', 'y_svy21']].to_numpy()
            b = active[['x_svy21', 'y_svy21']].to_numpy()
            squared = ((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2)
            closest = squared.argmin(axis=1)
            df.loc[indices, distance_col] = np.sqrt(squared[np.arange(len(a)), closest])
            if lag == 0:
                df.loc[indices, 'nearest_mrt_station'] = active.station_name.to_numpy()[closest]
    features = config['base_features'] + config['optional_transport_features'] + config['transport_sensitivity_features']
    require(config['target'] not in features and len(features) == len(set(features)), 'Unsafe feature list')
    require(df[features + [config['target']]].notna().all().all(), 'Missing model values')
    numeric = df[features].select_dtypes(include='number')
    require(np.isfinite(numeric.to_numpy()).all(), 'Nonfinite features')
    require((df[['resale_price', 'floor_area_sqm', 'remaining_lease_months']] > 0).all().all(), 'Nonpositive values')
    require(df.record_id.is_unique, 'Record IDs not unique')
    train_addresses = set(df.loc[df.split.eq('train'), 'address_key'])
    df['address_unseen_in_train'] = ~df.address_key.isin(train_addresses)
    report = ROOT / 'reports/model-data'
    report.mkdir(parents=True, exist_ok=True)
    for dimension in ['month', 'town', 'flat_type', 'match_status']:
        df.groupby(['split', dimension]).size().rename('rows').reset_index().to_csv(report / f'coverage-by-{dimension}.csv', index=False)
    summary = {
        'input_sha256': lineage, 'source_rows': len(df),
        'split_rows': df.split.value_counts().sort_index().to_dict(),
        'extra_identical_source_rows_retained': int(df.duplicated(raw_columns).sum()),
        'rows_in_repeated_groups': int(df.repeated_source_row.sum()),
        'unseen_address_rows_by_split': df.groupby('split').address_unseen_in_train.sum().astype(int).to_dict(),
        'quality_gates': 'passed: complete joins, valid parsing, finite features, positive target/area/lease, unique record IDs, chronological disjoint splits, complete station joins, active-service-only distance calculations',
        'test_policy': 'Counts and coverage only; no fitting, test targets summarised, or test scores computed.',
        'models_trained': 0
    }
    out = ROOT / 'data/processed/model-transactions.csv'
    df.to_csv(out, index=False, float_format='%.6f')
    summary['output_sha256'] = digest(out)
    (report / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
