"""Profile downloaded snapshots without dropping or repairing source records."""
import io
import json
import re
import zipfile
from pathlib import Path

import pandas as pd
import shapefile
from pyproj import CRS, Transformer

ROOT = Path(__file__).resolve().parents[1]


def normalise(series):
    return series.fillna("").str.upper().str.strip().str.replace(r"\s+", " ", regex=True)


def profile_csv(path):
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return df, {"rows": len(df), "columns": list(df.columns),
                "blank_counts": {col: int(df[col].str.strip().eq("").sum()) for col in df},
                "repeated_full_rows_after_first": int(df.duplicated().sum())}


def numeric_profile(series):
    numeric = pd.to_numeric(series, errors="coerce")
    return {"unparseable": int(numeric.isna().sum()), "non_positive": int(numeric.le(0).sum()),
            "min": float(numeric.min()), "median": float(numeric.median()),
            "max": float(numeric.max())}


def audit_transport(name):
    archive = zipfile.ZipFile(ROOT / "data/raw" / (name + ".zip"))
    stem = next(path[:-4] for path in archive.namelist() if path.endswith(".shp"))
    reader = shapefile.Reader(shp=io.BytesIO(archive.read(stem + ".shp")),
                              dbf=io.BytesIO(archive.read(stem + ".dbf")),
                              shx=io.BytesIO(archive.read(stem + ".shx")))
    records = pd.DataFrame([record.as_dict() for record in reader.records()])
    crs = CRS.from_wkt(archive.read(stem + ".prj").decode())
    transform = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    bbox = list(reader.bbox)
    # Only transform the bounding-box corners; this is an extent sanity check.
    result = {"features": len(reader), "geometry": reader.shapeTypeName,
              "fields": list(records.columns), "bbox_source": bbox,
              "bbox_corner_wgs84": [transform.transform(bbox[0], bbox[1]),
                                     transform.transform(bbox[2], bbox[3])],
              "crs_name": crs.name, "crs_unit": crs.axis_info[0].unit_name}
    for col in {"stations": ["LIN_NAM", "TYP_CD"],
                "bus_stops": ["STATUS", "SERVICE_TY"], "station_exits": []}[name]:
        result[col + "_counts"] = {str(k): int(v) for k, v in records[col].value_counts().items()}
    if name == "stations":
        result["unique_station_labels"] = int(records.STN_NAM.nunique())
        result["duplicate_station_label_rows"] = int(records.STN_NAM.duplicated().sum())
        result["labels_needing_station_code_review"] = sorted(
            x for x in records.STN_NAM.unique() if not re.fullmatch(r"(?:[A-Z]{2}\d+[A-Z]?)(?: / [A-Z]{2}\d+[A-Z]?)?", x))
    elif name == "station_exits":
        result["unique_station_names"] = int(records.stn_name.nunique())
        result["duplicate_name_exit_pairs"] = int(records.duplicated(["stn_name", "exit_code"]).sum())
    else:
        result["unique_stop_codes"] = int(records.BUS_STOP_N.nunique())
        result["duplicate_stop_code_rows"] = int(records.BUS_STOP_N.duplicated().sum())
    return result


def main():
    report = ROOT / "reports/phase0"
    report.mkdir(parents=True, exist_ok=True)
    resale, resale_stats = profile_csv(ROOT / "data/raw/resale.csv")
    properties, property_stats = profile_csv(ROOT / "data/raw/property.csv")
    resale["address_key"] = normalise(resale.block) + "|" + normalise(resale.street_name)
    properties["address_key"] = normalise(properties.blk_no) + "|" + normalise(properties.street)
    property_stats["duplicate_address_keys"] = int(properties.address_key.duplicated().sum())
    match = resale.address_key.isin(properties.address_key)
    unmatched = resale.loc[~match].groupby(["block", "street_name"], as_index=False).size()
    unmatched.to_csv(report / "unmatched-property-addresses.csv", index=False)
    join = {"matched_rows": int(match.sum()), "total_rows": len(resale),
            "matched_pct": float(match.mean() * 100), "unique_resale_addresses": int(resale.address_key.nunique()),
            "matched_unique_addresses": int(resale.loc[match, "address_key"].nunique())}
    months = resale.month.value_counts().sort_index()
    months.rename_axis("month").reset_index(name="transactions").to_csv(report / "monthly-counts.csv", index=False)
    resale_stats["month_min"] = months.index.min()
    resale_stats["month_max"] = months.index.max()
    resale_stats["invalid_months"] = int((~resale.month.str.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])")).sum())
    resale_stats["missing_months"] = sorted(set(pd.period_range(months.index.min(), months.index.max(), freq="M").astype(str)) - set(months.index))
    resale_stats["town_counts"] = {str(k): int(v) for k, v in resale.town.value_counts().items()}
    resale_stats["flat_type_counts"] = {str(k): int(v) for k, v in resale.flat_type.value_counts().items()}
    resale_stats["numeric"] = {col: numeric_profile(resale[col]) for col in ["resale_price", "floor_area_sqm", "lease_commence_date"]}
    lease = resale.remaining_lease.str.extract(r"^(\d+) years?(?: (\d+) months?)?$")
    resale_stats["unparseable_remaining_lease"] = int(lease[0].isna().sum())
    lease_months = pd.to_numeric(lease[0]) * 12 + pd.to_numeric(lease[1].fillna("0"))
    resale_stats["remaining_lease_months"] = numeric_profile(lease_months)
    storey = resale.storey_range.str.extract(r"^(\d+) TO (\d+)$")
    resale_stats["unparseable_storey"] = int(storey[0].isna().sum())
    resale_stats["reversed_storey_ranges"] = int((pd.to_numeric(storey[0]) > pd.to_numeric(storey[1])).sum())
    resale_stats["lease_start_after_transaction_year"] = int((pd.to_numeric(resale.lease_commence_date) > resale.month.str[:4].astype(int)).sum())
    summary = {"resale": resale_stats, "property": property_stats, "property_join": join,
               "transport": {name: audit_transport(name) for name in ["stations", "station_exits", "bus_stops"]}}
    building_path = ROOT / "data/raw/buildings.geojson"
    if building_path.exists():
        buildings = json.loads(building_path.read_text())
        features = buildings["features"]
        summary["buildings"] = {"features": len(features), "geometry_counts": pd.Series([f["geometry"]["type"] for f in features]).value_counts().to_dict(),
                                "property_keys_first_feature": list(features[0]["properties"]),
                                "first_feature_properties": features[0]["properties"]}
        b = pd.DataFrame([f["properties"] for f in features])
        summary["buildings"]["unique_postcodes"] = int(b.POSTAL_COD.nunique())
        summary["buildings"]["duplicate_block_street_code_pairs"] = int(b.duplicated(["BLK_NO", "ST_COD"]).sum())
        summary["buildings"]["unique_street_codes"] = int(b.ST_COD.nunique())
        summary["buildings"]["invalid_postcodes"] = int((~b.POSTAL_COD.astype(str).str.fullmatch(r"\d{6}")).sum())
        # Unique block numbers are candidate matches only, not verified address matches.
        unique_p = properties.loc[~properties.blk_no.duplicated(keep=False)]
        unique_b = b.loc[~b.BLK_NO.duplicated(keep=False)]
        candidate = unique_p.merge(unique_b, left_on="blk_no", right_on="BLK_NO", validate="one_to_one")
        summary["buildings"]["unique_block_number_candidate_pairs_unverified"] = len(candidate)
        candidate[["blk_no", "street", "ST_COD", "POSTAL_COD"]].head(20).to_csv(report / "coordinate-candidates-unverified.csv", index=False)
    resale.sort_values("floor_area_sqm", key=lambda x: pd.to_numeric(x), ascending=False).head(10).drop(columns="address_key").to_csv(report / "largest-floor-areas-review.csv", index=False)
    summary["snapshots"] = json.loads((ROOT / "data/raw/manifest.json").read_text())
    # Manifest is reproducibility metadata only; raw snapshots stay ignored.
    (report / "source-manifest.json").write_text(json.dumps(summary["snapshots"], indent=2) + "\n")
    (report / "audit-summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps({"resale_rows": len(resale), "join": join,
                      "transport_features": {k: v["features"] for k, v in summary["transport"].items()}}, indent=2))


if __name__ == "__main__":
    main()
