"""Download the Phase 0 snapshots; retain hashes, not temporary signed URLs."""
import argparse
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS = {
    "resale": ("d_8b84c4ee58e3cfc0ece0d773c8ca6abc", "csv"),
    "property": ("d_17f5382f26140b1fdae0ba2ef6239d2f", "csv"),
    "buildings": ("d_16b157c52ed637edd6ba1232e026258d", "geojson"),
}
LTA = {
    "stations": "TrainStation_Sep2026.zip",
    "station_exits": "TrainStationExit.zip",
    "bus_stops": "BusStopLocation_Sep2026.zip",
    "road_sections": "RoadSectionLine_Sep2026.zip",
}


def fetch(url):
    result = subprocess.run(["curl", "--fail", "--silent", "--show-error", "--location",
                             "--max-time", "180", url], capture_output=True)
    if result.returncode:
        raise RuntimeError("Download failed; curl exit " + str(result.returncode))
    return result.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    raw = ROOT / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    manifest_path = raw / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for name, (dataset_id, extension) in DATASETS.items():
        path = raw / (name + "." + extension)
        if path.exists() and not args.refresh:
            continue
        base = "https://api-open.data.gov.sg/v1/public/api/datasets/" + dataset_id
        # A ready public snapshot can already be polled. Initiate only if needed.
        result = json.loads(fetch(base + "/poll-download"))
        if not result.get("data", {}).get("url"):
            fetch(base + "/initiate-download")
            for _ in range(5):
                time.sleep(15)
                result = json.loads(fetch(base + "/poll-download"))
                if result.get("data", {}).get("url"):
                    break
        if not result.get("data", {}).get("url"):
            raise RuntimeError("Snapshot not ready: " + name)
        data = fetch(result["data"]["url"])
        path.write_bytes(data)
        manifest[name] = {"dataset_id": dataset_id, "file": path.name,
                          "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                          "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                          "source": "https://data.gov.sg/datasets/" + dataset_id + "/view"}
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        print(name, len(data), "bytes", flush=True)
        time.sleep(15)  # Respect the documented anonymous API quota.
    for name, filename in LTA.items():
        path = raw / (name + ".zip")
        if path.exists() and not args.refresh and name in manifest:
            continue
        url = "https://datamall.lta.gov.sg/content/dam/datamall/datasets/Geospatial/" + filename
        data = path.read_bytes() if path.exists() and not args.refresh else fetch(url)
        path.write_bytes(data)
        manifest[name] = {"file": path.name, "bytes": len(data),
                          "sha256": hashlib.sha256(data).hexdigest(), "source": url,
                          "retrieved_at_utc": datetime.now(timezone.utc).isoformat()}
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        print(name, len(data), "bytes", flush=True)


if __name__ == "__main__":
    main()
