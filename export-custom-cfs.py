"""
export-custom-cfs.py

Exports custom CFs from Sonarr/Radarr, filtering out any that are already
managed by Trash Guides (via recyclarr.yml). Saves custom-only CFs as
individual JSON files ready for configarr's localCustomFormatsPath.

Usage: python export-custom-cfs.py
"""

import json
import logging
import os
import re
import requests
import yaml
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────

CONFIG_PATH = "config.json"
RECYCLARR_YML = "recyclarr.yml"
LOG_DIR = "logs"

TRASH_GUIDES_BASE = "https://raw.githubusercontent.com/TRaSH-Guides/Guides/master/docs/json"

# ── Helpers ───────────────────────────────────────────────────────────────────

def setup_logging() -> str:
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ]
    )
    return log_file

def extract_trash_ids(yml_path: str) -> dict[str, list[str]]:
    """Parse recyclarr.yml and return {arr_type: [trash_id, ...]}"""
    with open(yml_path, "r") as f:
        config = yaml.safe_load(f)

    ids = {"sonarr": [], "radarr": []}

    for arr_type in ("sonarr", "radarr"):
        section = config.get(arr_type, {})
        for instance in section.values():
            for cf_block in instance.get("custom_formats", []):
                for tid in cf_block.get("trash_ids", []):
                    # Strip inline comments (e.g. "abc123 # Name")
                    clean = tid.split("#")[0].strip()
                    if clean:
                        ids[arr_type].append(clean)

    return ids


def fetch_trash_guide_names(trash_ids: list[str], arr_type: str) -> set[str]:
    """Fetch CF names from Trash Guides repo for the given trash_ids."""
    names = set()
    total = len(trash_ids)
    print(f"  Fetching {total} Trash Guide CF names for {arr_type}...")

    for i, tid in enumerate(trash_ids, 1):
        url = f"{TRASH_GUIDES_BASE}/{arr_type}/cf/{tid}.json"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                name = data.get("name", "").strip().lower()
                if name:
                    names.add(name)
            else:
                logging.warning(f"  [WARN] {tid}: HTTP {r.status_code}")
        except Exception as e:
            logging.warning(f"  [WARN] {tid}: {e}")

        if i % 10 == 0:
            logging.info(f"    {i}/{total}...")

    return names


def fetch_arr_cfs(base_url: str, api_key: str, arr_name: str) -> list[dict]:
    """Export all CFs from an arr instance via API."""
    url = f"{base_url.rstrip('/')}/api/v3/customformat"
    headers = {"X-Api-Key": api_key}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    cfs = r.json()
    logging.info(f"  Exported {len(cfs)} CFs from {arr_name}")
    return cfs


def save_cf(cf: dict, output_dir: str):
    """Save a single CF as a JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    # Sanitise filename
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', cf["name"])
    path = os.path.join(output_dir, f"{safe_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cf, f, indent=2, ensure_ascii=False)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log_file = setup_logging()
    start = datetime.now()
    logging.info("=== export-custom-cfs started ===")
    logging.info(f"Log: {log_file}")

    # Load config
    if not os.path.exists(CONFIG_PATH):
        logging.error(f"ERROR: {CONFIG_PATH} not found. Copy config.example.json to config.json and fill in your details.")
        input("\nPress Enter to exit...")
        return
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    instances = config["instances"]

    # Stage 1: Parse recyclarr.yml
    logging.info("Stage 1/3: Reading recyclarr.yml...")
    if not os.path.exists(RECYCLARR_YML):
        logging.error(f"ERROR: {RECYCLARR_YML} not found. Put it in the same folder as this script.")
        input("\nPress Enter to exit...")
        return
    trash_ids_by_type = extract_trash_ids(RECYCLARR_YML)
    for arr_type, ids in trash_ids_by_type.items():
        logging.info(f"  {arr_type}: {len(ids)} Trash Guide IDs found")

    # Stage 2: Fetch Trash Guide CF names
    logging.info("Stage 2/3: Fetching Trash Guide CF names from GitHub...")
    trash_names_by_type = {}
    for arr_type, ids in trash_ids_by_type.items():
        trash_names_by_type[arr_type] = fetch_trash_guide_names(ids, arr_type)
        logging.info(f"  {arr_type}: resolved {len(trash_names_by_type[arr_type])} names")

    # Stage 3: Export and filter CFs
    logging.info("Stage 3/3: Exporting CFs from arr instances...")
    for instance in instances:
        name = instance["name"]
        arr_type = instance["arr_type"]
        output_dir = instance["output_dir"]
        trash_names = trash_names_by_type.get(arr_type, set())

        logging.info(f"\n  [{name}]")
        try:
            all_cfs = fetch_arr_cfs(instance["base_url"], instance["api_key"], name)
        except Exception as e:
            logging.error(f"  ERROR connecting to {name}: {e}")
            continue

        saved = []
        skipped = []

        for cf in all_cfs:
            cf_name_lower = cf.get("name", "").strip().lower()
            if cf_name_lower in trash_names:
                skipped.append(cf["name"])
            else:
                save_cf(cf, output_dir)
                saved.append(cf["name"])

        logging.info(f"  Saved {len(saved)} custom CFs → {output_dir}/")
        logging.info(f"  Skipped {len(skipped)} Trash Guide CFs")

        if skipped:
            logging.info("  Skipped (Trash Guide):")
            for n in sorted(skipped):
                logging.info(f"    - {n}")

        if saved:
            logging.info("  Saved (custom):")
            for n in sorted(saved):
                logging.info(f"    + {n}")

    elapsed = (datetime.now() - start).seconds
    logging.info(f"\n=== Done in {elapsed}s. Copy custom-cfs/ into your configarr setup. Log: {log_file} ===")
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
