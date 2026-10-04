# Backup package 3.0 — development contract

Not a release. BMA 1.1.0 remains unchanged. Public README still describes the
historical release; use this document and V3_E2E.md for this branch.

## Verified sources

- Development base: `Home-Assistant-Backup-Manager` main
  `f7c582d52ca7f7bd89beac9ca1f3a249632ff1b0` (public package 1.0.1).
- Functional baseline: private `HA_backup` commit
  `47f9ab39e18d760ce9ea43557282f9afd86fafa1`, package 2.0.1,
  retention shell script, Home Assistant Backup cards in BACKUP, and
  Backup Location Periodic Check. Private configuration is not copied here.
- BMA tag 1.1.0: `161eeba96b50e2679c2849e948c306991506486a`;
  services, API specification, adapter, event tracker, coordinator, sensors,
  README and beta2 validation inspected.
- Evernote project contract revision 0.4 and explicit Work mandate, 2026-10-04.

## Responsibilities and registry

BMA implements create verification, inventory, classification, event deduplication
and GFS safety. The package owns schedules, policy, notifications and presentation.
All mutations and plans use one queued worker. Full/Partial entry scripts use
single mode to suppress duplicate calls while their job is queued/running.
Different jobs serialize. An external/native actor can still race the package:
BMA remains the final safety boundary. Queued work is not replayed after restart.

Destination selectors use `input_boolean.bma_backup_destination_<profile>_*`.
Each selector gets its `agent_id` from `homeassistant.customize`. YAML anchors
share each mapping among profiles. No provider list is embedded in runners or
health logic. Add a helper (no initial value), a customization, and a UI row per
profile that should offer the new destination. New helpers start OFF. Use a full
HA restart after editing the registry; isolated helper reloads can temporarily
leave missing customizations and will fail closed. Do not rename entity IDs.
An unavailable selector is an invalid configuration, even if its last state was OFF.

The external provider IDs are intentionally empty; configure from live BMA
`list_agents`. Local `hassio.local` is the OS/Supervised mapping validated with
BMA; other installation types must confirm/change it too. Registration alone is
not health: preflight refresh checks errors for selected agents. Out-of-scope
errors do not block a valid selected scope. No global completeness gate wrongly
blocks Local because S3 is down.

## Defaults and persistence

Contents and policy helpers omit `initial`. A one-time initializer sets all Full
contents ON, Partial HA/database ON, Full/Partial Local ON, provisional keep_last=3,
other counters zero, and leaves all schedules/automatic retention OFF. Its marker
is persistent; never reset it to reconfigure an existing installation. A newly
added destination is not auto-enabled. External retention scopes start empty/OFF.
HA-native and App Update have independent configurable scopes and counters;
App Update always groups per app. Apps content currently means all/none, matching
production v2; per-app selection is not implemented.

Real apply additionally requires a session unlock, reset OFF at each startup/reload.
This is an E2E guard, not a user permission/security boundary. Counters are
provisional, not an approved production policy. Empty/all-zero policies are rejected.

## Outcomes and events

Create uses BMA response verification, including job/class, all requested copies,
and empty failed-agent/content lists. Operational service errors leave an empty
response and are reported as failure; configuration/template errors remain in HA
logs. YAML has no general try/except. The worker disables stored traces because
passwords are resolved from `!secret ha_backup_password`; no password enters an
entity, report or notification. HA native SSL inclusion is retained. Database is
passed exactly as selected; HA/BMA validate unsupported content combinations.

Verified BMA events dispatch retention asynchronously into the same worker queue.
The worker rechecks enabled/unlocked state when execution begins and rejects any
selected agent not confirmed by the event. A newly selected destination therefore
cannot silently enter event-triggered cleanup. User changes before queued work
executes apply to that work; no destructive plan is cached. External event notifications
are separate; App Update and unknown diagnostics default OFF. Stable BMA does not
emit discovered unknown backups. Its event tracker owns deduplication/startup
baseline; a manually forged duplicate event is outside that contract.

Create success and retention outcome are separate notifications, preserving a
successful backup when cleanup fails. Actual retention can partially delete before
BMA raises: failure notification explicitly requests inventory/log inspection.
Trigger-based report sensors persist summary, scope and execution attributes;
failed attempts do not overwrite the last verified successful report. Status
records the failure separately. Plan candidate lists are not persisted; repeat
BMA plan_retention directly when detailed candidate inspection is required.

Health aggregates only enabled schedules/retention profiles. Manual Full/Partial
have separate readiness sensors. With no active jobs, aggregate ready means no
unsatisfied requirement; it does not mean every provider is healthy.

## Legacy coexistence caveat

Namespaces do not isolate the backup archive. Legacy v2 shell retention selects
ALL Supervisor backups without BMA source/job filtering. If legacy retention is
active, it can delete new v3 test backups. Its hourly location check can also report
Local tests as a network failure, and legacy name heuristics can duplicate external
notifications. This package does not modify those automations. Before live testing,
Paolo must choose a controlled window or explicitly pause legacy retention; no
claim of archive isolation is made. Both schedulers must not be enabled together.

The historical shell file remains in Git only; v3 never references it. Do not copy
it during v3 installation. Do not remove the live legacy package during initial E2E.

## Official syntax references checked

- https://www.home-assistant.io/docs/configuration/packages/
- https://www.home-assistant.io/integrations/homeassistant/ (customize)
- https://www.home-assistant.io/integrations/input_boolean/ (restore/default)
- https://www.home-assistant.io/docs/scripts/ (queue, responses, error handling)
- https://www.home-assistant.io/integrations/script/
- https://www.home-assistant.io/integrations/template/ (restored trigger attributes)
- https://www.home-assistant.io/docs/automation/trigger/
- https://www.home-assistant.io/docs/templating/
- https://www.home-assistant.io/dashboards/actions/
- https://www.home-assistant.io/dashboards/button/
- https://www.home-assistant.io/dashboards/history-graph/
