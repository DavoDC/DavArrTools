# DavArrTools

Utility scripts for Sonarr/Radarr arr management.

---

## export_custom_cfs.py

Exports your **custom-only** CFs from Sonarr/Radarr, ready to use with [configarr](https://github.com/raydak-labs/configarr).

Reads your `recyclarr.yml` to identify which CFs are managed by Trash Guides, then skips those — only saving CFs you made yourself.

### Requirements

```bash
pip install -r requirements.txt
```

> **Note:** If you forget, the script will auto-install missing packages on first run.

### Setup

1. Copy `recyclarr.yml` into the same folder as the script
2. Copy `config.example.json` to `config.json` and fill in your arr details:

```json
{
  "dry_run": false,
  "instances": [
    {
      "name": "Sonarr",
      "base_url": "http://YOUR_SONARR_IP:8989",
      "api_key": "YOUR_SONARR_API_KEY",
      "arr_type": "sonarr",
      "output_dir": "custom-cfs/sonarr",
      "force_include": [],
      "force_exclude": []
    }
  ]
}
```

Your API key is at `Settings → General → API Key` in Sonarr/Radarr. `config.json` is gitignored — credentials stay local.

### Run

```bash
python export_custom_cfs.py
```

### Output

```
custom-cfs/
├── sonarr/
│   ├── My Custom CF.json
│   └── Another Custom CF.json
└── radarr/
    └── My Radarr CF.json
```

Copy the `custom-cfs/` folder into your configarr setup and point `localCustomFormatsPath` at it.

### Config options

| Option | Description |
|--------|-------------|
| `dry_run` | Set to `true` to run without writing any files — useful for checking what would be saved/skipped |
| `force_include` | CF names to always save, even if they match a Trash Guide name |
| `force_exclude` | CF names to always skip, even if not in recyclarr.yml — useful for Trash CFs missing inline comments |

### What gets skipped

Any CF whose name matches one in your `recyclarr.yml` Trash Guide list is skipped — configarr pulls those automatically from Trash Guides, no local file needed.

If a Trash CF slips through (because its recyclarr.yml comment doesn't match the CF name exactly), add it to `force_exclude` in config.json.

A full list of skipped and saved CFs is printed at the end so you can verify the results.

---

## export_custom_profiles.py

Exports quality profiles from Sonarr/Radarr in configarr-compatible format.

Uses the same `config.json` as the CF exporter. Profiles are saved to `profiles_output_dir` (defaults to `custom-profiles/<arr_type>/` if not set).

### Run

```bash
python export_custom_profiles.py
```

### Output

```
custom-profiles/
├── sonarr/
│   └── My Profile.json
└── radarr/
    └── Another Profile.json
```

The script handles all format differences between the arr API and configarr:
- `cutoff` int ID → quality name string
- `language` object → name string
- Nested quality items → simplified `{name, allowed, items}` structure
- `formatItems` list → `{name: score}` dict

---

### Examples

See the `examples/` folder for reference JSON files:
- `custom-cf-example.json` — what a correctly exported custom CF looks like
- `trash-guide-cf-example.json` — Trash Guide CF format for comparison
- `force-exclude-example*.json` — examples of Trash CFs that may slip through without `force_exclude`
