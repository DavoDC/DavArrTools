"""
export_custom_cfs.py

Exports custom CFs from Sonarr/Radarr, filtering out any that are already
managed by Trash Guides (via recyclarr.yml). Saves custom-only CFs as
individual JSON files ready for configarr's localCustomFormatsPath.

Usage: python export_custom_cfs.py
"""

import json
import logging
import os
import re
import shutil
from datetime import datetime
from utils import ensure_requirements, setup_logging, fetch_arr_data

# ── Config ────────────────────────────────────────────────────────────────────

CONFIG_PATH = "config.json"
RECYCLARR_YML = "recyclarr.yml"

# Only these fields are needed by configarr — everything else from the arr API is dropped
KEEP_FIELDS = {"name", "includeCustomFormatWhenRenaming", "specifications"}
KEEP_SPEC_FIELDS = {"name", "implementation", "negate", "required", "fields"}

# ── Helpers ───────────────────────────────────────────────────────────────────


def extract_trash_names(yml_path: str) -> dict[str, set[str]]:
    """
    Parse recyclarr.yml and extract CF names from inline comments.
    Format: '- abc123def # CF Name Here'
    Returns {arr_type: {cf_name_lower, ...}}
    """
    names = {"sonarr": set(), "radarr": set()}

    with open(yml_path, "r") as f:
        raw = f.read()

    for arr_type in ("sonarr", "radarr"):
        pattern = rf"^{arr_type}:\s*$(.*?)(?=^\w|\Z)"
        match = re.search(pattern, raw, re.MULTILINE | re.DOTALL)
        if not match:
            continue
        block = match.group(1)

        for line in block.splitlines():
            m = re.match(r'\s*-\s+[a-f0-9]{32}\s+#\s+(.+)', line)
            if m:
                name = m.group(1).strip().lower()
                if name:
                    names[arr_type].add(name)

    return names


def fetch_arr_cfs(base_url: str, api_key: str, arr_name: str) -> list[dict]:
    """Export all CFs from an arr instance via API."""
    cfs = fetch_arr_data(base_url, api_key, "customformat")
    logging.info(f"  Exported {len(cfs)} CFs from {arr_name}")
    return cfs


def _clean_spec(spec: dict) -> dict:
    """Strip arr-internal fields from a specification, keeping only what configarr needs."""
    out = {k: v for k, v in spec.items() if k in KEEP_SPEC_FIELDS}
    # arr returns 'fields' as a list [{name, order, value, ...}]; configarr wants {value: ...}
    if "fields" in out:
        raw = out["fields"]
        if isinstance(raw, list):
            out["fields"] = {"value": raw[0]["value"]} if raw else {}
        elif isinstance(raw, dict) and "value" in raw:
            out["fields"] = {"value": raw["value"]}
    return out


def save_cf(cf: dict, output_dir: str):
    """Save a CF as a JSON file, stripping arr-internal fields."""
    os.makedirs(output_dir, exist_ok=True)
    clean = {k: v for k, v in cf.items() if k in KEEP_FIELDS}
    if "specifications" in clean:
        clean["specifications"] = [_clean_spec(s) for s in clean["specifications"]]
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', cf["name"])
    path = os.path.join(output_dir, f"{safe_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2, ensure_ascii=False)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ensure_requirements()
    log_file = setup_logging("export_cfs")
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
    dry_run = config.get("dry_run", False)

    if dry_run:
        logging.info("*** DRY RUN MODE — no files will be written ***")

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

    # Stage 2: Export CFs from each instance
    t2 = datetime.now()
    logging.info("\nStage 2/3: Exporting CFs from arr instances...")
    all_results = {}
    for instance in instances:
        name = instance["name"]
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
        force_include = {n.lower() for n in instance.get("force_include", [])}
        force_exclude = {n.lower() for n in instance.get("force_exclude", [])}

        # Clear output dir so re-runs are clean
        if not dry_run and os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            logging.info(f"  Cleared existing output dir: {output_dir}/")

        saved = []
        skipped = []
        force_saved = []
        force_excluded = []

        for cf in all_cfs:
            cf_name_lower = cf.get("name", "").strip().lower()
            is_trash = cf_name_lower in trash_names
            is_forced = cf_name_lower in force_include
            is_excluded = cf_name_lower in force_exclude

            if (is_trash and not is_forced) or is_excluded:
                skipped.append(cf["name"])
                if is_excluded and not is_trash:
                    force_excluded.append(cf["name"])
            else:
                if not dry_run:
                    save_cf(cf, output_dir)
                if is_forced and is_trash:
                    force_saved.append(cf["name"])
                else:
                    saved.append(cf["name"])

        logging.info(f"\n  [{name}] Saved {len(saved)} custom CFs -> {output_dir}/")
        if force_saved:
            logging.info(f"  [{name}] Force-included {len(force_saved)} (matched Trash Guide name but kept):")
            for n in sorted(force_saved):
                logging.warning(f"    ! {n}  ← same name as Trash Guide CF — verify this is intentional")
        if force_excluded:
            logging.info(f"  [{name}] Force-excluded {len(force_excluded)} (manually listed in force_exclude):")
            for n in sorted(force_excluded):
                logging.info(f"    x {n}")
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
    if dry_run:
        logging.info(f"\n=== Dry run complete in {elapsed}s. No files written. Log: {log_file} ===")
    else:
        logging.info(f"\n=== Done in {elapsed}s. Copy custom-cfs/ into your configarr setup. Log: {log_file} ===")
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
