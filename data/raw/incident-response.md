# Incident Response Playbook

Defined severity levels and response procedures for Acme Corp services.

## Severity Definitions

| Level | Impact | Response Time | Goal |
|---|---|---|---|
| P1 | Service down or data loss | < 5 minutes | Restore within 1 hour |
| P2 | Major feature degraded | < 15 minutes | Restore within 4 hours |
| P3 | Minor issue, no user impact | < 1 business day | Fix within 1 week |

## P1: Sev-1 Procedure

1. **Declare** — Post in #incidents on Slack. Include service name and impact.
2. **Assemble** — On-call engineer(s) join a huddle immediately. Escalate to the engineering manager.
3. **Mitigate** — Rollback, feature-flag off, or scale up. Mitigation over root cause.
4. **Communicate** — Update #incidents every 15 minutes. Post to status.acme.internal.
5. **Resolve** — When service is restored, close the incident and schedule a post-mortem within 48 hours.

## P2: Sev-2 Procedure

1. **Triage** — Open a Jira ticket with the `sev-2` label. Assign to the service owner.
2. **Investigate** — Root cause analysis during business hours. Mitigate within 4 hours.
3. **Fix** — Standard PR cycle. Include regression tests.
4. **Post-mortem** — Lightweight: what happened, why, what changed.

## P3: Sev-3 Procedure

- Log as a regular Jira ticket.
- Fix during the next sprint unless priority changes.
- No post-mortem required.

## On-Call Rotation

Two-week rotations per team. Handover happens every other Friday at 16:00. The outgoing on-call documents any active issues in the #oncall-handover channel.

## Escalation Path

Engineer → Senior Engineer → Engineering Manager → VP of Engineering
