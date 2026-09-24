# Launch plan template

File: `invai-docs/growth/launches/<YYYY-MM>-<slug>/plan.md` (when growth-marketer is inactive: the path the tech
lead set on the card, for example `invai-docs/product/launches/…` for the PM)

```
# Launch: <one line: what, for whom, where>
Tier: 1 / 2 / 3.  Target date: <date or "approval + N days"> [owner to confirm].  Lead: <role>
Status: planning / gates open / go (OI-…) / launched <date> / held <date, why>

## Gates
| Area | Gate | Owner role | Evidence | Status |
|---|---|---|---|---|
| Product | In scope.md; release-checklist done; golden path green on the release SHA | product-manager, qa-engineer | links | |
| Product | Known issues listed with workarounds | customer-success | customers/issues.md | |
| Compliance | Marketplace approval granted | compliance-officer | packets/<m>/packet.md status | |
| Compliance | Listing and claims reviewed; legal docs published by owner | compliance-officer | claims.md, OI-… | |
| Security | No open High findings; incident plan written | security-reviewer, platform-sre | security/…, ops/… | |
| Ops | SLOs, alerts and capacity for the launched path | platform-sre | ops/… | |
| Support | Help articles EN/ES, macros, onboarding checklist | docs-writer, customer-success | help/…, customers/… | |
| Measurement | Events and metrics defined; review scheduled | data-analyst | metrics/… | |

## Calendar
| Day | Item | Owner role | Output | OI draft |
|---|---|---|---|---|
| T-28 | Positioning and page drafts start | growth-marketer | growth/pages/… | |
| T-21 | Listing draft + screenshots; email sequence | growth-marketer | … | |
| T-14 | Reviews (PM, designer, compliance) | … | … | |
| T-10 | Release notes draft; help articles | docs-writer | … | |
| T-7 | All owner drafts queued | all | | OI-… |
| T-2 | Go/no-go | owner (PM recommends) | OI-… | |
| T-0 | Owner publishes and sends | owner | | |
| T+1 | Watch errors, signups, tickets | platform-sre, customer-success | | |
| T+7 | Readout 1 | growth-marketer + data-analyst | this file | |
| T+30 | Readout 2 + lessons | same | this file, team/lessons.md | |

## Success metrics
| Metric (definition link) | Target | Measured when |

## Hold rule
Pause signups / listing if: <Sev1 incident; golden-path failure; marketplace warning; …>. Decided by the owner. Drafted notice: OI-…

## Pre-mortem
| Failure | Likelihood | Mitigation | Owner |

## Readouts
### T+7
### T+30
```
