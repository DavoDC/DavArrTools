# DavArrTools

Utility scripts for Sonarr/Radarr arr management.

---

## export-custom-cfs.py

Exports your **custom-only** CFs from Sonarr/Radarr, ready to use with [configarr](https://github.com/raydak-labs/configarr).

Reads your `recyclarr.yml` to identify which CFs are managed by Trash Guides, then skips those — only saving CFs you made yourself.

### Requirements

```bash
pip install requests pyyaml
```

### Setup

1. Copy `recyclarr.yml` into the same folder as the script
2. Open `export-custom-cfs.py` and fill in your arr details at the top:

```python
INSTANCES = [
    {
        "name": "Sonarr",
        "base_url": "http://YOUR_SONARR_IP:8989",
        "api_key": "YOUR_SONARR_API_KEY",
        ...
    },
    ...
]
```

Your API key is at `Settings → General → API Key` in Sonarr/Radarr.

### Run

```bash
python export-custom-cfs.py
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

### What gets skipped

Any CF whose name matches one in your `recyclarr.yml` Trash Guide list is skipped — configarr pulls those automatically from Trash Guides, no local file needed.

A full list of skipped CFs is printed at the end so you can verify nothing was incorrectly excluded.
