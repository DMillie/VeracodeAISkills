# Evidence

The skills hold rules. This folder holds how each rule is known, so a person can audit it and a
change to a skill can be checked against it. Nothing here is packaged into a `.skill` file.

| File | What it holds |
|---|---|
| `register/<PREFIX>.md` | one row per evidence ID: basis, date checked, source or observation, the claim as first recorded, the file it came from |
| `INDEX.md` | generated: every ID, its basis and date, and the files that cite it |
| `lab-runs.md` | the lab runs behind the 2026-11 skills: what worked, what did not, what was never tested |
| `verified-locally-2026-11-12.md` | the table of behaviours executed on the lab host that day (component, pins, policy flags) |

## How a citation reads in a skill

`[PS-04]` observed on a real tenant or in the lab. `[INT-12~]` read from documentation, a spec or
source code, not run. `[UPL-02?]` carried over from older notes and not re-verified.

The suffix must agree with the `Basis` column (`lab`, `docs`, `source`, `dated`, `carried`).

## Cross-checking

```bash
python3 tools/evidence.py check
```

Fails when a skill cites an ID that has no entry, an entry is cited nowhere, a suffix disagrees
with the basis, or an old-style dated tag is left in a skill.

```bash
python3 tools/evidence.py stale 180
```

Lists entries checked more than 180 days ago, and every `carried` entry.

## Changing a fact

1. Edit the rule in the skill (`shared/` first if the file lives there, then `tools/sync_shared.py sync`).
2. Add or update the register row: new date, what was observed or which page was read.
3. A fact that was re-verified live changes basis to `lab` and loses its `~` or `?` in the skill.
4. `python3 tools/evidence.py check && python3 tools/evidence.py index`.

## Known limits of this split

- The `Claim` column is the wording at the time of the split (2026-11-17). It is not kept in
  step with later edits to the rule; the ID is the link.
- `reference/integration/*.md` in the 2026-11 skills is a research snapshot whose source column
  is part of the content. It was left as it is.
- `playbook/04-packaging.md` still carries "proven on" notes inside its table. They were left
  until the behaviour suite has a baseline, because that table decides packaging outcomes.
- The lab's raw evidence (scan result files, pipeline logs, agent reports) is not in this
  repository. It stays with the lab that produced it.
