# DavArrTools — Future Ideas

## ⚠️ May Be Superseded (2026-03-10)

Ben is considering using **[profilarr](https://github.com/Dictionarry-Hub/profilarr)** instead of building a custom DavArrTools GUI/docker solution. Profilarr is a ready-made tool for managing and syncing Radarr/Sonarr quality profiles and custom formats.

**Implication:** If Ben goes with profilarr, DavArrTools GUI/docker work may not be needed at all. Hold off on any DavArrTools GUI or Docker work until Ben decides. The existing export scripts are still useful as a fallback or migration tool.

**To decide:** Does profilarr cover Ben's use case fully? If yes, DavArrTools becomes low priority or obsolete.

---

## Ben's Endgame Vision (2026-03-10)

Ben is thinking about a more polished end product once the export scripts are stable. Two options floated:

**Option A — Watered-down GUI**
- Simple GUI wrapping the current scripts
- Sonarr + Radarr only (no other arrs)
- Buttons: Push, Pull, Sync
- Much simpler scope than full configarr

**Option B — Docker with scheduled sync**
- Containerised version that runs on a schedule
- No GUI needed — set and forget
- Probably easier to deploy and maintain long-term

**Status:** Just an idea — don't implement yet. Worth keeping in mind when designing the scripts (keep them modular/scriptable so a GUI or scheduler can wrap them easily).

## Sync & Version Control Discussion (2026-03-10)

Further chat with Ben on how sync would work:
- Ben has the best configs and CFs — Ben is the master server/source of truth
- Sync direction: Ben's arrs → David's arrs (Ben pushes to David, not the other way)
- Git recommended for safety + change history — GitLab if Ben prefers over GitHub
- Could do without git but not ideal
- CLI program to auto-push changes on command — "easily done"
- GUI could still use DavArrTools scripts underneath (underlying arrtools as backend)
- Ben open to pros/cons of scheduled sync vs GUI approach

**Key decision pending:** scheduled sync (docker/CLI) vs GUI with push/pull/sync buttons. Likely CLI-first, GUI later if wanted.
