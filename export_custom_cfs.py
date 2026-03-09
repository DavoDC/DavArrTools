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
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def extract_trash_names(yml_path: str) -> dict[str, set[str]]:
    """
    Parse recyclarr.yml and extract CF names from inline comments.
    Format: '- abc123def # CF Name Here'
    Returns {arr_type: {cf_name_lower, ...}}
    """
    names = {"sonarr": set(), "radarr": set()}

    with open(yml_path, "r") as f:
        raw = f.read()

    # Find each arr section and extract commented names
    for arr_type in ("sonarr", "radarr"):
        # Find the section block
        pattern = rf"^{arr_type}:\s*$(.*?)(?=^\w|\Z)"
        match = re.search(pattern, raw, re.MULTILINE | re.DOTALL)
        if not match:
            continue
        block = match.group(1)

        # Extract all trash_id lines with comments: '- <hash> # <name>'
        for line in block.splitlines():
            m = re.match(r'\s*-\s+[a-f0-9]{32}\s+#\s+(.+)', line)
            if m:
                name = m.group(1).strip().lower()
                if name:
                    names[arr_type].add(name)

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
    t1 = datetime.now()
    logging.info("\nStage 1/3: Reading recyclarr.yml...")
    if not os.path.exists(RECYCLARR_YML):
        logging.error(f"ERROR: {RECYCLARR_YML} not found. Put it in the same folder as this script.")
        input("\nPress Enter to exit...")
        return
    trash_names_by_type = extract_trash_names(RECYCLARR_YML)
    for arr_type, names in trash_names_by_type.items():
        logging.info(f"  {arr_type}: {len(names)} Trash Guide CF names found")
    logging.info(f"  Stage 1 done in {(datetime.now() - t1).seconds}s")

    # Stage 2: Export and filter CFs from each instance
    t2 = datetime.now()
    logging.info("\nStage 2/3: Exporting CFs from arr instances...")
    all_results = {}
    for instance in instances:
        name = instance["name"]
        arr_type = instance["arr_type"]
        logging.info(f"  [{name}]")
        try:
            all_results[name] = (instance, fetch_arr_cfs(instance["base_url"], instance["api_key"], name))
        except Exception as e:
            logging.error(f"  ERROR connecting to {name}: {e}")
    logging.info(f"  Stage 2 done in {(datetime.now() - t2).seconds}s")

    # Stage 3: Filter and save
    t3 = datetime.now()
    logging.info("\nStage 3/3: Filtering and saving custom CFs...")
    for name, (instance, all_cfs) in all_results.items():
        arr_type = instance["arr_type"]
        output_dir = instance["output_dir"]
        trash_names = trash_names_by_type.get(arr_type, set())

        saved = []
        skipped = []

        for cf in all_cfs:
            cf_name_lower = cf.get("name", "").strip().lower()
            if cf_name_lower in trash_names:
                skipped.append(cf["name"])
            else:
                save_cf(cf, output_dir)
                saved.append(cf["name"])

        logging.info(f"\n  [{name}] Saved {len(saved)} custom CFs → {output_dir}/")
        logging.info(f"  [{name}] Skipped {len(skipped)} Trash Guide CFs")

        if skipped:
            logging.info("  Skipped (Trash Guide):")
            for n in sorted(skipped):
                logging.info(f"    - {n}")

        if saved:
            logging.info("  Saved (custom):")
            for n in sorted(saved):
                logging.info(f"    + {n}")

    logging.info(f"  Stage 3 done in {(datetime.now() - t3).seconds}s")

    elapsed = (datetime.now() - start).seconds
    logging.info(f"\n=== Done in {elapsed}s. Copy custom-cfs/ into your configarr setup. Log: {log_file} ===")
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
