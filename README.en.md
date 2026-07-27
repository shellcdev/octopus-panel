> 📌 Version: v3.1.37 | Updated: 2026-07-22 | Maintainer: 石叔 (Shell)
>
> 🌐 This is the English edition of the navigation hub. The authoritative Chinese version is **[README.md](README.md)**.

# Octopus Panel · Navigation Hub

> Onboarding entry point for new users and operators. Read in priority order — do not skip levels.

---

## 🔴 Must-Read (before first use)

| # | File | What to read | When |
|---|---|---|---|
| 1 | `SKILL.md` | Overview, hard/soft rules, four discussion modes, interaction commands | First use |
| 2 | `references/jargon.md` | Plain-language glossary (style-lock / soft-spot / tag / growth system) | First use |

---

## 🟡 Recommended (when generating / joining a discussion)

| File | What to read | When |
|---|---|---|
| `references/templates.md` | Role-card format, spawn prompt, discussion-board format, phase-summary format | Before generating a role |
| `references/role-templates.md` | Verified role template library (8 groups, 36 roles) | When generating a role |
| `references/discussion-examples.md` | 19 full discussion cases (+3 edge +1 diagnostic) | Quality check / format reference |

---

## 📂 File Map

### Core files

- **SKILL.md** — Overview, hard/soft rules, four discussion modes, 🎩 round filter, interaction commands, feedback channel
- **README.md** (Chinese) / **README.en.md** (this file) — Navigation hub
- **CHANGELOG.md** — Version change history
- **config.md** — Runtime config (5 categories, 17 keys total: paths 6 / role-source 3 / role-growth 4 / relationship-network 2 / output-and-verify 2)

### references/ directory

| File | Content | When to reference |
|---|---|---|
| `jargon.md` | Plain-language glossary (incl. v3.0 growth-system terms) | First use |
| `rules-discussion.md` | Discussion rules (roll-call / board / summary / convergence / hat-compat / anomaly scenarios 1-12) | During a discussion |
| `summary-format.md` | Summary formats (4 types) + quantitative judgment + scorecard | Summary phase |
| `roles-rules.md` | Role management (select / add / substitute / template library / tag filtering) | Generating/replacing a role |
| `rules-collab.md` | Collaboration & recovery (multi-person / L1-L3 / archiving) | Collaboration scenarios |
| `templates.md` | Standard template reference (incl. 🎩 hat-round Prompt template) | Before generating a role |
| `role-templates.md` | Role template library (8 groups, 36 roles) | When generating a role |
| `discussion-examples.md` | 19 full discussion cases (+3 edge +1 diagnostic) | Quality check / format reference |
| `role-templates-archive.md` | Retired/merged role template history backup | Checking historical templates |
| `auto-tag-rules.md` | 🆕 Auto-tag rules (8 tags + confidence formula + lifecycle) | Growth-system auto-tag judgment (off by default) |
| `growth-formula.md` | 🆕 Growth-system quantitative formula (EXP/level/decay/influence/achievement) | Growth-data tuning or audit (off by default) |

### scripts/ directory

| Script | Purpose |
|---|---|
| `growth_api.py` | 🆕 Role-growth core data layer (7 APIs: stance / relationship / achievement / tag / EXP / inject / backup) |
| `growth_tool.py` | 🆕 Growth-system ops entry (`backup`/`migrate`/`render`; merged from growth_backup/migrate/render) |
| `role_export.py` | 🆕 Role-market export/import (with desensitization) |
| `discussion_archive.py` | Archive discussion to knowledge base + scorecard computation + auto growth-data update |
| `role_generate.py` | Generate a draft role card from problem keywords |
| `role_validate.py` | Role-card quality validation (required fields + heuristic risk checks) |
| `role_test.py` | Role spawn test (generates a test Prompt) |
| `tag_filter.py` | Role tag filter (multi-condition AND match) |
| `audit.py` | 🆕 Doc/consistency audit entry (`docs`/`alias`/`orphans`/`all`; merged from audit_all/docs/orphans + role_verify_alias) |
| `audit_links.py` | 🆕 Link-health scan (re-scan dead refs; 0 real dead links to pass, historical refs exempt) |

---

## 🚀 Quick Start

### 🚀 Open-source users: install first

This repo *is* the skill source. To load it in a client, drop it into that client's `skills/` directory. Full steps (clone paths for OpenClaw / WorkBuddy, verification commands) live in the Chinese **[README.md](README.md)** → "快速上手 / 开源用户：先安装". In short:

```bash
git clone https://github.com/shellcdev/octopus-panel.git
cp -r octopus-panel ~/.qclaw/skills/        # OpenClaw  (Windows: %USERPROFILE%\.qclaw\skills\)
# or  ~/.workbuddy/skills/octopus-panel/     # WorkBuddy
```

### First use (5 min)

1. Read the first 200 lines of `SKILL.md` (overview + hard rules + four modes)
2. Read `references/jargon.md` to understand the terminology (2 min)
3. Just throw a question at 石叔 — he'll walk you through a full run

### Before generating a role (10 min)

1. Read `references/templates.md` for the standard role-card format
2. Read `references/role-templates.md` and pick a suitable role template
3. For dynamic generation → read the dynamic-generation SOP in `templates.md`

### When debugging role quality

1. Read the pre-flight risk-control three-questions in `references/role-templates.md`
2. Read the quantitative-judgment section in `references/summary-format.md`
3. Compare format and quality against `references/discussion-examples.md`

---

## 🌱 Role Growth System (off by default · opt-in)

> **Disabled by default** — this is intentional design, not a bug.

- **Default behavior**: `config.md` sets `role_source_mode = generate`; every role is dynamically generated per session and discarded after use, without writing `growth_record.json`. Therefore stance history / achievements / relationship network / auto-tags do **not** accumulate under the default config.
- **How to enable (pick one)**:
  1. Change `config.md`: `role_source_mode = local_priority` (prefer reusing roles with growth history; shortfall handled per `pure_generated_handling`); to actually surface the relationship network, also set `relationship_network_enabled = true`.
  2. Manual promotion: a pure-generated role is tagged `suggest_localize` at archive time; save it to the library per the prompt to make it persistent, carrying growth history from the next session.
- See `references/growth-formula.md` (quantitative formula) and `references/auto-tag-rules.md` (tag rules) for details.

---

## 🛠️ Operations Guide

### Maintenance & audit

1. After editing roles/rules/version, run `python scripts/audit.py all` for doc consistency + alias validation
2. After adding/removing files in `scripts/` or `references/`, run `python scripts/audit_links.py` to re-scan link health (0 real dead links to pass; CHANGELOG historical refs are compliant exemptions); if you renamed a file, sync the README script table and the SKILL.md index
3. Growth data is auto-backed-up after each archive via `discussion_archive.py` calling `growth_api.auto_backup_if_needed()` (≥24h once, keeps `backup_keep_count` rolling copies); manual full backup: `python scripts/growth_tool.py backup --backup`, restore: `backup --restore <file>`
4. Export/import roles (role market): `python scripts/role_export.py <role_id>` / `--import-file <json>`
5. Before promoting a new role, run `python scripts/role_test.py --role-card <card.json> --test-question "..."` to generate a style-lock self-check prompt

### Add a role template

1. Append under the relevant group in `references/role-templates.md`
2. Must pass the pre-flight risk-control three-questions
3. Record it in `CHANGELOG.md`

### Add a discussion case

1. Append in `references/discussion-examples.md`
2. Label "Case N", discussion question, full transcript, 石叔's summary
3. Record it in `CHANGELOG.md`

---

## 🎨 Emoji Semantic Convention

> Emojis in the docs are not decoration — they are **visual semantic markers**. Each face maps to a fixed information type, used consistently throughout, not swapped arbitrarily.

### Semantic overview

| Emoji | Semantic role | Definition | Example usage |
|---|---|---|---|
| 📌 | Meta info | Version, update, maintainer and other doc metadata | Top-of-doc version statement |
| 🐙 | Project identity | Octopus Panel brand symbol, entry hint | First-use guide |
| 🔴 | Strong alert | Must-read / high-risk / non-skippable | 🔴 Must-read, hard rules |
| 🟡 | Medium alert | Recommended / caution / semi-forced | 🟡 Suggestion, soft rules |
| 🟢 | Light alert | Optional / nice-to-have | 🟢 Optional reference |
| 🎩 | Feature plugin | Special feature module marker (six-hat filter) | Round filter, feature switch |
| 🧩 | Feature module | System feature, scheduling, mechanism component | Schedule preset, schedule gear |
| 🎨 | Visual marker system | 🆕 Emoji semantic convention itself, marker-system overview | Emoji semantic section |
| 🔘 | Switch control | Config switch, mode toggle | Relationship-network switch |
| 🚀 | Quick action | Quick start, cheat-sheet, shortcut | Quick-start guide |
| 🌱 | Growth system | Role growth, data, tags | Role growth system note |
| 🛠️ | Ops tool | Maintenance ops, scripts, audit | Ops guide, script notes |
| 🤝 | Collaboration | Multi-person collab, contribution, community | Contribution guide |
| 📬 | Feedback channel | Feedback, issue reporting | Feedback entry |
| ⚠️ | Warning/violation | Rule violation, risk hint | Hard rule, ⚠️ marker |
| 💡 | Viewpoint/point | Core view, key info | Previous-round view summary |
| 📜 | Resume/history | Stance record, historical data | Stance-resume injection |
| 🔍 | Verify/check | Reference check, fact check | Reference-check command |
| 🆕 | New marker | Doc/feature addition (incl. changelog) | references/scripts new entries |
| 📂 | File/directory | File nav, directory structure | File map |

### Usage rules

1. **Uniqueness**: each emoji's semantic role is unique across the doc — one emoji never means multiple things
2. **Fixed position**:
   - Section heading: left of the title (e.g. `## 🔴 Must-Read`)
   - In-body emphasis: right after the keyword (e.g. `rule⚠️`)
   - Meta-info line: alone at line start (e.g. `> 📌 Version: v3.1.14`)
3. **No repeat**: no more than 2 emojis per line (avoid visual noise)
4. **No abuse**: don't use emojis without a clear semantic role
5. **New-emoji approval**: to add a new emoji meaning, first record it in CHANGELOG.md and update this convention

---

## 🤝 Contribution Guide

Feedback and submissions welcome. **How to submit:** open a [GitHub Issue](https://github.com/shellcdev/octopus-panel/issues) or send a Pull Request (see [CONTRIBUTING.md](CONTRIBUTING.md) for the dev setup and PR checklist). For security vulnerabilities, private-report via [SECURITY.md](SECURITY.md) — do **not** open a public issue.

- New role template (must pass pre-flight risk-control three-questions)
- New discussion case (must be complete, with edge scenarios)
- Rule optimization (must state rationale + impact scope)
- Doc-error fixes (typo, broken link, formatting)

---

## 📬 Feedback Channel

Finished and something felt off?

**As a user** — just say **"反馈：[your comment]"** during a discussion and 石叔 will note it for next time.

**As an open-source contributor** — submit via GitHub:
- Open a [GitHub Issue](https://github.com/shellcdev/octopus-panel/issues) (bug / feature / question)
- Or fork and open a Pull Request — see [CONTRIBUTING.md](CONTRIBUTING.md) for the dev setup and PR checklist
- Security vulnerability? Private-report via [SECURITY.md](SECURITY.md) — **do not** open a public issue

Common issues (as a user):
- Role speech too templated → tell me, I'll add soft-spots and post-trigger states
- Discussion went off-topic → tell me, I'll improve the diagnostic step
- Want a vertical-industry role (e.g. medical / legal / education) → tell me, I'll add it to the template library
