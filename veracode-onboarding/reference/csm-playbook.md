# CSM playbook — running a Veracode onboarding

For whoever owns the rollout: a Veracode customer success manager, or a customer's
AppSec lead taking Veracode to many teams. Everything here is a starting
structure — tailor it to what you know about the customer, and mark what you
assumed so it is confirmed rather than discovered late.

Milestones M1–M6 are defined in `SKILL.md` §5. Technical steps live in the other
reference files; this file is about sequencing, people and communication.

---

## 1. Readiness questionnaire — send before the kickoff

Short enough to be answered. Group the questions, and skip any you already know.

**Account and access**
- Which Veracode region is the account in — Commercial, European or US Federal?
- Who will be the Veracode Administrator, and who the Security Lead(s)?
- Is sign-in through SSO?
- Which products are licensed — Static, SCA, Container Security, DAST?

**Code and builds**
- Where does code live — GitHub.com, GitHub Enterprise Server, GitLab.com or
  self-managed, Azure DevOps, Bitbucket? Who is an organization/group owner there?
- Roughly how many repositories and deployable applications are in scope first?
- Main languages and build tools, by share of the portfolio?
- Anything unusual to build — monorepos, C/C++, mobile, legacy?

**Pipelines and network**
- Which CI systems run the builds? Hosted or self-hosted runners?
- Does outbound traffic need allowlisting (Veracode IP ranges)?
- Where are CI secrets kept (CI secret store, vault)?

**Scope and goals**
- What does success look like in 90 days — coverage, PR feedback, a compliance
  number for leadership, an audit deadline?
- Which 2–3 applications should go first? (Representative languages; owners who
  are willing.)
- How should Veracode results map to teams — by product, by business unit?

## 2. Kickoff — 60 minutes

| Min | Item | Leave with |
|---|---|---|
| 10 | Goals and success criteria | The 90-day outcome, in their words |
| 10 | Current state from the questionnaire | Confirmed SCM, CI, region, licences, languages |
| 15 | Path decision (`SKILL.md` §2) | Repo scanning vs CI pipelines vs both; Container Security yes/no |
| 10 | Access and credentials plan | Named admins; API service account owner; where secrets go |
| 10 | Pilot applications and dates | 2–3 apps, owners, target date for first results (M2) |
| 5 | Decisions log and next steps | Owners and dates for each action |

**Decisions to force at kickoff** — each one is expensive to change later:

1. **Profile naming** — one convention, before any integration creates profiles.
2. **Break-build stance** — report-only first, or blocking from day one on agreed
   repos; and the date it tightens.
3. **Scan naming** — how release builds are named, so release reporting works.
4. **Who triages** — a named owner per application for findings and mitigations.

## 3. Onboarding plan — phases with exit criteria

Durations are typical, not promises; adjust to team size and how fast access
requests move in their organisation.

| Phase | When | Work | Exit when |
|---|---|---|---|
| 0 · Prepare | Before kickoff | Questionnaire; admin accounts; network allowlisting requested | Questionnaire answered; admins can sign in |
| 1 · Foundation | Week 1 | Teams; API service account with the right roles; HMAC credentials in the secret store; policy chosen; first app scanned by hand | **M1**, **M2** |
| 2 · Integrate | Weeks 2–3 | Repository scanning on the pilot repos, or CI jobs; baseline; profile and scan naming applied | **M3**, **M4** for the pilot apps |
| 3 · Scale | Weeks 4–6 | Widen `include_repos` or roll the CI template out in batches; packaging fixes per language | **M5** — coverage known, gaps named |
| 4 · Operate | Week 6+ | Triage cadence; mitigation workflow; compliance reporting; credential-expiry reminder; tighten gates | **M6** |

Run 30/60/90-day reviews against these exit criteria, not against activity.

## 4. Tracker — one row per application or repository

Suggested columns. In Claude, build it as a spreadsheet or task list the CSM can
edit and share.

| Column | Values |
|---|---|
| Application / repo | name |
| Owning team | name |
| SCM / CI | e.g. GitHub, ADO |
| Main language | |
| Path | repo scanning · CI · manual |
| Profile name | as agreed |
| Policy | name |
| Packaging verified | yes · no · issue |
| First scan | date |
| Latest policy verdict | passed · conditional · did not pass · not assessed |
| PR feedback | off · report-only · blocking |
| Results in Platform | yes · no (repo scanning: `analysis_on_platform`) |
| Blocker / next action | free text, with an owner |

## 5. Measures of progress

Measure things the Platform can show, and report the trend:

- **Time to first result** (kickoff → M2).
- **Coverage:** in-scope applications with a policy scan in the last 30 days;
  repositories with PR feedback.
- **Policy assignment:** applications with a deliberate policy (not the default by
  accident).
- **Compliance rate** — report it, but do not set a target in month one; the first
  number mostly measures the backlog.
- **Gate health:** repos with PR feedback that are still on after 30 days.

## 6. Where onboardings stall — and what unsticks them

| Stall | Move |
|---|---|
| Waiting on SCM org-owner access or PATs | Ask at kickoff who the owner is; book 30 minutes with them for the install itself |
| Automation set up with a person's keys | Create the API service account now; regenerate and move secrets before that person is on leave |
| First scan "clean" | Treat as a packaging question: check the prescan, the modules and the lock files |
| Results "missing" | Check where they should appear: Pipeline Scan is local; repo scanning needs `analysis_on_platform: true`; sandboxes don't change compliance |
| Developers angry at red builds | Baseline, report-only for a period, then gate on Very High only |
| Duplicate application profiles | Apply the naming convention; merge or retire the extras early, before history accumulates |
| Self-hosted runners time out | Network allowlisting for Veracode IPs; it is not an outage |
| Pipelines break overnight, months later | Credentials expired (one year) or were regenerated elsewhere; put expiry on a calendar |
| US Federal customer expecting repo scanning | Not available in that region; go straight to CI pipelines |
| Leadership asks for a trend line in week 2 | History accumulates from the first scans; show coverage and the first verdicts now, and set a date for the first trend |

## 7. Messages — skeletons to fill

Fill these with the customer's specifics; keep each short.

**Kickoff invitation** — purpose in one line; agenda (§2); who must attend (admin,
SCM owner, a pilot app owner); the questionnaire attached with a due date.

**Weekly status**

```
Milestone: M2 (first results) — on track / at risk
Done this week:   …
Next week:        …
Blocked on:       … (owner, since when)
Decision needed:  … (by whom, by when)
```

**Before the first gate turns on (to developers)** — what changes and when; where
results appear (PR check, Security tab, issues); that only **new** flaws fail the
build; how to get help, and how mitigations are proposed.

**30/60/90 review** — milestones reached with dates; coverage numbers; what is
blocked; the decisions needed to reach the next milestone.
