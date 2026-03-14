# Configarr Setup — Custom CF + Profile Sync

Configarr already does everything needed:
- Syncs Trash Guide CFs
- Syncs your custom CFs (from local files)
- Syncs quality profiles
- Multiple instances in one config (one-way: master → others)
- Free + open source

Repo: https://github.com/raydak-labs/configarr

---

## Folder Structure

```
configarr/
├── docker-compose.yml
├── config/
│   ├── config.yml
│   └── secrets.yml
├── repos/          ← cache, leave empty
└── custom-cfs/     ← your exported CF JSON files go here
```

---

## Step 1 — Export your custom CFs from Sonarr/Radarr

Use the API to export all custom formats at once:

**Sonarr:**
```
GET http://YOUR_SONARR_IP:8989/api/v3/customformat?apikey=YOUR_API_KEY
```

**Radarr:**
```
GET http://YOUR_RADARR_IP:7878/api/v3/customformat?apikey=YOUR_API_KEY
```

Open that URL in your browser — you'll get a JSON array. Save each custom format as a separate `.json` file in the `custom-cfs/` folder.

---

## Step 2 — Create `docker-compose.yml`

```yaml
services:
  configarr:
    image: ghcr.io/raydak-labs/configarr:latest
    container_name: configarr
    environment:
      - TZ=Europe/London
    volumes:
      - ./config:/app/config
      - ./repos:/app/repos
      - ./custom-cfs:/app/cfs
```

---

## Step 3 — Create `config/secrets.yml`

```yaml
SONARR_MASTER_KEY: your_sonarr_api_key
RADARR_MASTER_KEY: your_radarr_api_key
SONARR_INSTANCE2_KEY: other_sonarr_api_key
RADARR_INSTANCE2_KEY: other_radarr_api_key
```

---

## Step 4 — Create `config/config.yml`

```yaml
localCustomFormatsPath: /app/cfs

sonarr:
  master_sonarr:
    base_url: http://YOUR_SONARR_IP:8989
    api_key: !secret SONARR_MASTER_KEY
    custom_formats:
      - trash_ids:
          - PUT_TRASH_IDS_HERE
        quality_profiles:
          - name: YOUR_PROFILE_NAME

  instance2_sonarr:
    base_url: http://OTHER_SONARR_IP:8989
    api_key: !secret SONARR_INSTANCE2_KEY
    custom_formats:
      - trash_ids:
          - PUT_TRASH_IDS_HERE
        quality_profiles:
          - name: THEIR_PROFILE_NAME

radarr:
  master_radarr:
    base_url: http://YOUR_RADARR_IP:7878
    api_key: !secret RADARR_MASTER_KEY

  instance2_radarr:
    base_url: http://OTHER_RADARR_IP:7878
    api_key: !secret RADARR_INSTANCE2_KEY
```

---

## Step 5 — Run

```bash
docker-compose run --rm configarr
```

Run this whenever you want to sync. Schedule with a cron job to automate.

---

## Notes

- Your custom CFs just need to be in `custom-cfs/` — configarr picks them up automatically
- Trash Guide CFs are fetched automatically from the Trash Guides repo
- This is one-way: your config is the master, it pushes to other instances
- API keys: `Settings → General → API Key` in Sonarr/Radarr
