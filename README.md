# Home Assistant Backup Manager 3.0

> **Development candidate — not a release yet.**  
> This branch contains the BMA-based v3 rewrite and is ready for controlled Local E2E testing. Do not enable production schedules or real retention until the E2E gates in `docs/V3_E2E.md` are completed.

Home Assistant Backup Manager 3.0 is a Home Assistant YAML package that adds policy, scheduling, notifications, retention controls, and a Lovelace management UI on top of **Backup Manager Actions (BMA) 1.1.0**.

The v3 architecture deliberately stops talking directly to the Supervisor backup API. Backup creation, inventory, classification, multi-agent verification, events, and safe GFS retention are delegated to BMA.

## Architecture

```text
Home Assistant Backup Manager
        ↓
Backup Manager Actions 1.1
        ↓
pkg_backup_home_assistant 3.0
        ↓
Lovelace dashboard
```

- **BMA** is the capability and safety layer.
- **This package** owns scheduling, policy, orchestration, notifications, and UI state.
- **Lovelace** is presentation and human control only; the package works without the dashboard.

## Current development status

Branch: `feature/bma-backup-package-3.0`

The package has been validated headlessly with Home Assistant 2026.9.4 / Python 3.14.7:

- 31 package tests passed.
- 9 upstream BMA event-tracker tests passed.
- Real BMA/provider I/O was simulated; no live backup deletion was performed.
- Browser rendering and real provider behavior remain E2E checks.

See:

- `docs/V3_DEVELOPMENT.md` — architecture and design decisions.
- `docs/V3_VALIDATION.md` — executed test evidence.
- `docs/V3_E2E.md` — controlled live E2E procedure.

## Requirements

- Home Assistant with YAML packages enabled.
- Backup Manager Actions **1.1.0** installed and loaded.
- Home Assistant version compatible with BMA 1.1.0; the v3 runtime tests were executed on HA 2026.9.4.
- A `ha_backup_password` key in `secrets.yaml`. Home Assistant resolves the secret at configuration load even when password use is disabled.
- Optional Pushover service `notify.pushover_hassio` if Pushover notifications are enabled.

## Repository layout

```text
package/
  pkg_backup_home_assistant.yaml   # v3 package
  ha_backup_frontend.yaml          # native Lovelace E2E dashboard

docs/
  V3_DEVELOPMENT.md
  V3_VALIDATION.md
  V3_E2E.md

tests/
  test_v3_runtime.py
  requirements.txt
```

There is **no retention shell script in v3**. Retention is handled only through BMA `plan_retention` and `apply_retention`.

## Main features

### Full and Partial jobs

Both jobs expose the same content selectors:

- Home Assistant
- Database
- Apps / Add-ons
- `addons/local`
- `media`
- `share`
- `ssl`

Initial defaults:

| Content | Full | Partial |
| --- | --- | --- |
| Home Assistant | ON | ON |
| Database | ON | ON |
| Apps / Add-ons | ON | OFF |
| Local add-ons | ON | OFF |
| Media | ON | OFF |
| Share | ON | OFF |
| SSL | ON | OFF |

Manual and scheduled execution use the same runners:

- `script.bma_backup_run_full`
- `script.bma_backup_run_partial`

BMA metadata uses stable job IDs:

- `job_id: full`
- `job_id: partial`

### Backup destinations

The package is prepared for:

- Local
- SMB / Network
- Google Drive
- S3 Compatible

Initial destination defaults for both Full and Partial:

- Local: ON
- SMB / Network: OFF
- Google Drive: OFF
- S3 Compatible: OFF

External provider IDs are intentionally left empty until they are read from the live BMA `list_agents` response.

Destination selectors follow:

```text
input_boolean.bma_backup_destination_<profile>_*
```

Each selector receives its BMA `agent_id` through `homeassistant.customize`. Runners discover enabled selectors dynamically by prefix, so adding a destination does not require changing create, retention, or health logic.

### Scheduling

Full and Partial have independent:

- enable switches;
- time selectors;
- day presets.

The current presets are:

- Never
- Every day
- Mon - Wed - Fri
- Mon and Fri
- Saturday
- Sunday

Automatic schedules start OFF during migration/E2E.

### Retention

The package exposes separate policies for:

- Full
- Partial
- HA Native
- App Update

Each policy supports:

- `keep_last`
- daily
- weekly
- monthly
- yearly

Full and Partial are isolated by `source_type=bma` plus their own `job_id`, so they do not compete in the same GFS buckets.

HA Native and App Update retention are independently scoped and start OFF. App Update uses per-app grouping.

Dry-run calls:

```text
backup_manager_actions.plan_retention
```

Real apply calls:

```text
backup_manager_actions.apply_retention
```

All retention calls use an explicit agent scope.

During the current E2E phase, real apply is additionally protected by:

```text
input_boolean.bma_backup_apply_unlocked
```

which resets OFF at startup. This is a development/E2E interlock and must be reviewed before final production automation.

### Backup events and notifications

The package listens to:

```text
backup_manager_actions_backup_created
```

and handles:

- BMA Full
- BMA Partial
- HA Native
- App Update
- diagnostic unknown/unrecognized events

The v3 package does not classify backups using filename prefixes, last-known slugs, or Supervisor polling.

Pushover and persistent notifications are supported. App Update and unknown notifications are optional to avoid noise.

### Health

Health is evaluated against the destinations required by enabled profiles, not against every registered provider.

A broken unselected S3 provider must not block a Local-only Full or Partial job.

## Safe migration from the legacy package

The v3 entity namespace is intentionally separate:

```text
bma_backup_*
```

so it can coexist temporarily with the production legacy package.

For the initial E2E:

1. Keep the legacy package installed.
2. Copy `package/pkg_backup_home_assistant.yaml` to a **different filename**, for example:
   `/config/packages/pkg_bma_backup.yaml`.
3. Keep new automatic schedules OFF.
4. Keep new automatic retention OFF.
5. Keep real apply locked.
6. Temporarily disable legacy automatic retention during the test window because the legacy shell cleanup does not understand BMA source/job metadata and can delete v3 test backups.
7. Test Partial Local first, then Full Local, then dry-run and failure cases.

Follow `docs/V3_E2E.md` exactly before any real deletion.

## Frontend

`package/ha_backup_frontend.yaml` is a standalone **test dashboard** built only with native Home Assistant cards.

It exposes:

- package and destination health;
- latest backup and archive state;
- Run Full / Run Partial;
- Full and Partial scheduling/content/destination controls;
- retention profile and GFS controls;
- Future Simulation (Dry Run);
- Last Actual Run;
- archive-size history.

It is intentionally an E2E UI, not yet the final polished release dashboard.

## Security and failure behavior

The package is designed to fail closed where uncertainty could cause unwanted backup creation or deletion:

- selected agents are validated before operations;
- unknown/unavailable selectors are rejected;
- BMA create responses are verified;
- failed copies or failed content prevent package retention from following a failed create;
- retention scope is validated against the BMA response;
- automatic retention never expands to an agent not confirmed by the triggering backup event;
- the password is referenced only through `!secret ha_backup_password`;
- worker traces are disabled so the resolved password is not stored in traces.

## Legacy history

The `main` branch still contains the historical 1.x release. The actual production 2.0.1 baseline used to design v3 lives in Paolo's Home Assistant configuration backup and is documented in the project notes.

Legacy implementation artifacts are intentionally **not copied into the v3 development branch**. Git history and `main` remain available for historical reference.

## License

MIT
