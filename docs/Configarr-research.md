# Friend's Program Request — Custom CF + Profile Sync for Arrs

*Saved from conversation — 2026-03-09*

## What they want

A tool like recyclarr but that syncs **both**:
1. Custom Formats (CFs) from Trash Guides (these have a `trash-id`)
2. **Their own custom CFs** (not from Trash Guides)

Also wants to sync **entire quality profiles**, not just CFs. Their profiles score CFs very differently from Trash Guide defaults.

Goal: keep multiple arr instances in sync without manual work.

## Context

- Friend maintains a shared arr config for a small group
- Currently uses recyclarr for Trash Guide CFs
- Custom CFs and custom profiles require manual syncing — that's the pain point
- Configarr (`https://github.com/raydak-labs/configarr`) may already do this — needs investigation

## How recyclarr works

1. Pulls latest CF definitions from Trash Guides JSON repo
2. Compares against current CFs in your arr instances
3. Updates any that have changed

So the sync logic is: fetch source → diff against live arr state → push changes.
A custom tool would do the same but also include custom CFs + profiles (stored somewhere) in step 1.

**Quality profiles are also in the Trash Guides JSON** — recyclarr syncs those too.

## Preferred Format
- Console app (not webapp) — simpler
- UI inspiration: notifiarr (https://notifiarr.wiki/) — paywalled, but open source UI patterns can be copied freely
- Goal: free + open source

## Arr Instances
- Sonarr and Radarr need syncing across multiple instances
- Test plan: change a CF on one arr manually, run tool, verify it syncs to the other instance
- **Sync direction**: one-way — one instance is master, pushes to others

## Investigation Questions

1. Does configarr sync custom (non-Trash-Guide) CFs?
2. Does it sync entire quality profiles (with custom scoring)?
3. Could it replace recyclarr entirely?
4. How does recyclarr grab the latest Trash Guide CFs? (see `https://github.com/recyclarr/recyclarr`)

## Links

- recyclarr: https://github.com/recyclarr/recyclarr
- configarr: https://github.com/raydak-labs/configarr
- Trash Guide CF source data (JSON): https://github.com/TRaSH-Guides/Guides/tree/master/docs/json — recyclarr pulls from here

## Configarr Investigation Result — BUILD NOT NEEDED

Configarr already does everything needed:
- ✅ Syncs Trash Guide CFs
- ✅ Syncs custom/local CFs (defined as local YAML files or inline config)
- ✅ Syncs quality profiles
- ✅ Multiple arr instances in one config (named instances with separate API keys)
- ✅ Sonarr v4 + Radarr v5
- ✅ Free + open source

**Recommendation: set up configarr instead of building a new tool.**

## Easiest way to define custom CFs for configarr
Two options:
1. **Export from existing arr** — Radarr/Sonarr has API to export CFs as JSON; save those files locally; configarr reads them via `localCustomFormatsPath`. Easiest since CFs are already defined in the arr.
2. **Inline YAML** — define CFs directly in configarr's YAML config. More work to set up initially.

**Recommendation:** export CFs from arr via API → save as JSON files → point configarr at them. One-time setup, then configarr handles sync from there.

## Next Steps
- Help set up configarr with custom CFs + all instances
- See `Documents/Configarr-setup.md` for full setup guide
