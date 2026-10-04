# V3 development validation — 2026-10-04

## Executed

`python -m pytest tests/test_v3_runtime.py -q`

**31 passed**: 30 parameter-expanded behavioral cases using Home Assistant
2026.9.4 on Python 3.14.7, plus one namespace/frontend/static check. Test runtime
17.02 seconds in the development container. Dependency deprecation warnings were
present. This is a headless integration test, not live Supervisor/provider E2E.

The actual package YAML is loaded through HA bootstrap, with the real input
helpers, scripts, automations, template rendering, event bus, state machine and
restore-state storage. Tests assert those package integrations loaded. BMA I/O and
Pushover are simulated; no real backup or deletion is performed. Network/frontend
services are not part of the tested runtime. Frontend YAML is parsed and checked
against defined entities; browser rendering remains a live E2E check.

| Scenario | Evidence |
| --- | --- |
| Partial manual Local | HA/database ON, apps/folders OFF, job_id=partial, success, no apply |
| Full manual Local + password | All selectors passed, job_id=full; password absent from reports/notices |
| No destination | No create, explicit failure |
| Unmapped selector | No create, explicit failure |
| Provider absent | No create, explicit failure |
| Provider inventory error | No create, explicit failure |
| Backup Manager busy | No create, explicit failure |
| Unknown destination state | No create, explicit failure |
| Simulated partial create exception | Failure, no apply |
| Malformed create response | Failure, no apply |
| Out-of-scope S3 error | Local create succeeds |
| Full/Partial dry-run | Separate source/job filters and explicit Local scope; structured report |
| Locked apply | No BMA apply call |
| Unlocked simulated apply | Current policy passed directly; actual-run report |
| Partial apply exception | Failure; previous actual report preserved |
| Initialization repeated | Existing selector choice not reset |
| Full/Partial schedule disabled | Automation conditions prevent create |
| Full/Partial verified events | Correct isolated apply policy |
| HA Native event | No job_id field; explicit separate scope |
| App Update event | group_by=app, no job_id field |
| Unknown/unrecognized BMA job | No retention |
| Health transitions | Selected errors cause failure/recovery; unselected errors excluded |
| Added destination | Discovered automatically without runner changes |
| Scope changed after event | Newly selected unconfirmed agent blocks automatic apply |
| Unknown encryption selector | No unintentional unencrypted create |
| Concurrent Full/Partial and event apply | Serialized; repeated same-job invocation suppressed |
| Real runtime restart | Content choice/report restored; apply locked; no replay |
| Static namespace/frontend | New IDs consistent, native cards only, no shell/polling path |

## Review findings resolved

- `initial` would reset user settings: replaced with guarded one-time initialization.
- Arbitrary helper attributes are unsupported: mappings use core customization.
- Provider registration is insufficient: fresh scoped error checks precede operations.
- YAML `stop: ... error: true` is handled internally by HA: tests verify outcomes
  and side effects instead of expecting a propagated Python exception.
- Domain-wide state discovery can rate-limit template refreshes; health tests allow
  HA's update interval. Action preflight resolves current state directly.
- An encryption helper in unknown/unavailable state now blocks create.
- Changed event scope fails closed instead of cleaning an unconfirmed new agent.
- Regex used by the static test originally excluded digits and truncated `s3`;
  corrected test to recognize valid entity IDs. YAML itself was correct.

## Remaining live checks

- Actual agent IDs, Local disk space, backup encryption and restore readability.
- Real BMA create response/event against installed Supervisor and providers.
- Pushover delivery and visual dashboard rendering.
- HA installation-specific entity naming and package merge with the live legacy.
- Legacy retention interference: legacy shell can delete BMA backups; agree on a
  controlled window before creating live test backups.
- Real deletion, production GFS approval, scheduler activation and legacy retirement
  are intentionally not performed. See V3_E2E.md.

No merge, tag or release has been created. BMA and HA_backup remain unchanged.

## BMA event boundary verification

Also executed the unchanged upstream `tests/test_events.py` from BMA stable
1.1.0 at `161eeba96b50e2679c2849e948c306991506486a`: **9 passed** (0.04 s).
This verifies the delegated startup/deduplication boundary separately; those
upstream tests are not copied into the package repository and BMA is not modified.
