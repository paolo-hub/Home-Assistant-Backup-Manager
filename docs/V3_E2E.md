# Local E2E handoff — do not activate production schedules yet

This branch is a development candidate, not a release. No live backup operation
or deletion has been performed by development tests.

## Before installation

1. Keep BMA stable 1.1.0 installed. Confirm HA 2026.9.4 or a compatible newer build.
2. Read V3_DEVELOPMENT.md, especially legacy archive interference. Check whether
   legacy automatic retention is ON and whether a scheduled legacy job will run
   during testing. Paolo must explicitly approve any temporary pause. Do not run
   tests while legacy shell retention can delete test backups unexpectedly.
3. Save the current HA configuration/dashboard using your normal procedure.
4. Copy `package/pkg_backup_home_assistant.yaml` to
   `/config/packages/pkg_bma_backup.yaml` (different name from legacy).
   No shell retention script is part of v3. Packages must already be enabled with
   `homeassistant: packages: !include_dir_named packages`.
5. The existing secret key `ha_backup_password` must exist in `secrets.yaml`, even
   with password use OFF, because HA resolves secrets at configuration load.
   Reuse its existing value. Never paste it into Git, events, logs, or reports.
6. Execute BMA `backup_manager_actions.list_agents` in Developer Tools > Actions,
   returning the response. Confirm Local mapping `hassio.local`. Configure each
   external `agent_id` once in the YAML customization anchors when ready. Empty
   provider IDs are deliberate; leave external selectors OFF for initial tests.
7. Confirm these BMA entity IDs exist. New BMA installations can have different
   defaults; adapt presentation references if necessary:
   `sensor.backup`, `sensor.destinazioni_backup`, `sensor.ultimo_backup`,
   `sensor.backup_bma`, `sensor.backup_ha_nativi`, `sensor.backup_aggiornamento_app`,
   `sensor.dimensione_archivio_backup`. The global health entity is not used as a
   selected-scope gate.
8. Check configuration, then restart HA. Registry/helper/template changes require
   a complete restart for this first installation. Do not enable schedules.

## Defaults, UI and persistence

- Confirm all new entities use `bma_backup_`, with no `_2` duplicates.
- Full contents all ON; Partial only Home Assistant/database ON.
- Local ON for Full/Partial; external providers OFF. External retention profiles
  have no destination ON. Automatic Full/Partial and all retention OFF.
- `input_boolean.bma_backup_apply_unlocked` must be OFF.
- Import `package/ha_backup_frontend.yaml` as a NEW test dashboard through the raw
  configuration editor. Alternatively copy its sole view to the existing dashboard.
  Do not replace the existing BACKUP view. Only native cards are required.
- Change a non-destructive selector, restart, verify persistence and restore it.
  Initialization must not reapply defaults. Session apply unlock must remain OFF.
- After a YAML registry change, restart. Do not rename IDs in the UI. A new provider
  must start OFF and require no runner changes.

## Manual Local creation

1. Confirm automatic schedules/retention OFF and real apply locked.
2. Run `script.bma_backup_run_partial` first (smaller initial test).
3. Record returned event `backup_manager_actions_backup_created` without secrets,
   BMA `get_backup` readback, actual contents, Local copy, notification and package
   status. Expected source=bma, job_id=partial. No retention service should run.
4. Run `script.bma_backup_run_full`; verify source=bma, job_id=full and selected
   contents. Account for disk space before a Full backup.
5. Verify encrypted status with password selector ON if desired; confirm restore
   key availability independently. SSL can be included implicitly with HA ON.
6. Full/Partial overlap must serialize; repeated clicks of the same job while its
   runner is active must not start duplicate copies. Logs may show single-mode
   rejection. No queued operation should replay after restart.

## Safe failure tests

- Turn all destinations OFF for one profile and run it: explicit failure, no create.
- Enable an external selector whose mapping is still empty: explicit failure,
  no create. Restore it OFF afterward.
- Test provider-error handling only using a disposable/mocked provider or an
  explicitly approved failure scenario; do not disrupt production storage.
- Check a broken but unselected S3 does not block a healthy Local job.
- With schedule enable OFF, passing its configured time must not create a backup.
- Check BMA/native/app events do not duplicate on restart. App notifications
  default OFF; unknown never enters automatic retention.
- Selected-scope health should transition once on failure/recovery; a provider
  outside enabled profile requirements must not generate unhealthy status.

## Dry-run only

Select Full then Partial in Retention profile, choose Dry Run. Confirm considered,
keep, delete, out_of_scope, reclaimable bytes and completeness against a direct BMA
plan_retention response with identical scope/policy. No files must be deleted.
The persistent Future Simulation report is separate from Last Actual Run.
A failed plan updates operation status but does not forge a new successful report.
Inspect detailed candidate IDs through BMA's direct structured response when needed.

Try Apply Retention while the session unlock is OFF: it must stop before BMA apply.
STOP HERE. Do not unlock it as part of initial E2E.

## Later explicit approval gates

After reviewing the evidence with Paolo: decide production GFS values, authorize
a disposable Local-only real retention test, verify out-of-scope preservation,
then separately decide legacy retirement, schedule activation, merge and release.
HA-native/App Update remain optional and OFF until their explicit scopes/policies
are reviewed. S3 provider troubleshooting remains outside this package project.

No live apply, automatic scheduler enable, legacy removal, merge, tag or release
is authorized by this handoff.
