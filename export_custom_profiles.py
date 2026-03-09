"""
export_custom_profiles.py

Exports quality profiles from Sonarr/Radarr and saves them as individual JSON
files in a format compatible with configarr's localQualityProfilesPath.

Transforms the arr API format to the configarr/Trash Guides format:
  - cutoff: int ID → quality name string
  - language: object → name string
  - items: nested quality objects → simplified {name, allowed, items} structure
  - formatItems: list of {name, score} → {name: score} dict

Usage: python export_custom_profiles.py
"""

import json
import logging
import os
import re
import shutil
from datetime import datetime
from utils import setup_logging, fetch_arr_data

# ── Config ────────────────────────────────────────────────────────────────────

CONFIG_PATH = "config.json"

# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_quality_name(items: list, quality_id: int) -> str | None:
    """Search items (including nested groups) for a quality by ID, return its name."""
    for item in items:
        if "quality" in item:
            if item["quality"]["id"] == quality_id:
                return item["quality"]["name"]
        elif "items" in item:
            found = _find_quality_name(item["items"], quality_id)
            if found:
                return found
    return None


def _transform_item(item: dict) -> dict:
    """Convert one arr API quality item to configarr format."""
    if "quality" in item:
        # Single quality
        return {"name": item["quality"]["name"], "allowed": item["allowed"]}
    else:
        # Quality group
        out = {"name": item["name"], "allowed": item["allowed"]}
        sub_names = [i["quality"]["name"] for i in item.get("items", []) if "quality" in i]
        if sub_names:
            out["items"] = sub_names
        return out


def transform_profile(profile: dict) -> dict:
    """
    Transform an arr API quality profile to configarr format.
    Strips internal fields and converts all sub-structures to their simpler forms.
    """
    items = profile.get("items", [])
    cutoff_name = _find_quality_name(items, profile["cutoff"]) or str(profile["cutoff"])

    return {
        "name": profile["name"],
        "upgradeAllowed": profile["upgradeAllowed"],
        "cutoff": cutoff_name,
        "minFormatScore": profile.get("minFormatScore", 0),
        "cutoffFormatScore": profile.get("cutoffFormatScore", 0),
        "minUpgradeFormatScore": profile.get("minUpgradeFormatScore", 1),
        "language": profile["language"]["name"] if isinstance(profile["language"], dict) else profile["language"],
        "items": [_transform_item(i) for i in items],
        "formatItems": {fi["name"]: fi["score"] for fi in profile.get("formatItems", [])},
    }


def save_profile(profile: dict, output_dir: str):
    """Save a transformed profile as a JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', profile["name"])
    path = os.path.join(output_dir, f"{safe_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log_file = setup_logging("export_profiles")
    start = datetime.now()
    logging.info("=== export-custom-profiles started ===")
    logging.info(f"Log: {log_file}")

    if not os.path.exists(CONFIG_PATH):
        logging.error(f"ERROR: {CONFIG_PATH} not found. Copy config.example.json to config.json and fill in your details.")
        input("\nPress Enter to exit...")
        return
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    instances = config["instances"]
    dry_run = config.get("dry_run", False)

    if dry_run:
        logging.info("*** DRY RUN MODE — no files will be written ***")

    # Stage 1: Export profiles from each instance
    t1 = datetime.now()
    logging.info("\nStage 1/2: Exporting profiles from arr instances...")
    all_results = {}
    for instance in instances:
        name = instance["name"]
        logging.info(f"  [{name}]")
        try:
            raw = fetch_arr_data(instance["base_url"], instance["api_key"], "qualityprofile")
            logging.info(f"  Exported {len(raw)} profiles from {name}")
            all_results[name] = (instance, raw)
        except Exception as e:
            logging.error(f"  ERROR connecting to {name}: {e}")
    logging.info(f"  Stage 1 done in {(datetime.now() - t1).seconds}s")

    # Stage 2: Transform and save
    t2 = datetime.now()
    logging.info("\nStage 2/2: Transforming and saving profiles...")
    for name, (instance, raw_profiles) in all_results.items():
        output_dir = instance.get("profiles_output_dir",
                                  os.path.join("custom-profiles", instance["arr_type"]))

        if not dry_run and os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            logging.info(f"  Cleared existing output dir: {output_dir}/")

        saved = []
        for profile in raw_profiles:
            transformed = transform_profile(profile)
            if not dry_run:
                save_profile(transformed, output_dir)
            saved.append(transformed["name"])

        logging.info(f"\n  [{name}] Saved {len(saved)} profiles → {output_dir}/")
        for n in sorted(saved):
            logging.info(f"    + {n}")

    logging.info(f"  Stage 2 done in {(datetime.now() - t2).seconds}s")

    elapsed = (datetime.now() - start).seconds
    if dry_run:
        logging.info(f"\n=== Dry run complete in {elapsed}s. No files written. Log: {log_file} ===")
    else:
        logging.info(f"\n=== Done in {elapsed}s. Copy custom-profiles/ into your configarr setup. Log: {log_file} ===")
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
