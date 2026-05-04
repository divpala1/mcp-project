# Task: Generate end-user documentation

You are writing documentation for **Daitics AI CDP** — a [one-line description, e.g. "self-hosted note-taking app"]. The docs will live in the AI server.

## Who this is for
**End users of the app — not developers.** Assume the reader wants to *use* the app, not understand how it works internally. Many will be non-technical.

## How the docs will be consumed
Two ways, and both matter:
1. **Humans** — reading top-to-bottom or jumping in via search.
2. **An MCP server** — chunking these files and retrieving sections to answer user questions inside their AI assistants.

Because of (2), **every section must be self-contained and retrievable**:
- Headings should read like things a user would actually search for ("How to reset your password", not "Authentication").
- Repeat the subject inside the section. Write "To export data from the dashboard…" not "To export it…" — chunks lose the context above them.
- One topic per section. If a section starts covering two tasks, split it.
- No forward/backward references ("as mentioned above", "see below") — name the actual section by title.
- **Front-load the answer; the first sentence must stand alone.** If the first 200 characters of a section were retrieved with no surrounding context — no heading, no parent file, no page title — they should already start answering the question the heading implies. The MCP server retrieves at the section level; the first sentence is what an LLM grades the section on.

## Step 1 — Discovery (do this before writing anything)
1. Read `README.md`, the package manifest (`package.json` / `pyproject.toml` / etc.), and any existing docs.
2. Explore the codebase and identify:
   - Every user-facing feature (pages, screens, commands, UI flows).
   - Every action a user can take (buttons, forms, CLI commands, settings, keyboard shortcuts).
   - Configuration the *user* (not the developer) needs to set.
   - Error messages users will encounter and what they mean.
   - External integrations and what the user needs to do to connect them.
3. Output a **feature inventory** as a markdown checklist. Flag anything ambiguous about whether it's user-facing or developer-facing.
4. **Stop and wait for my review** before writing docs.

## Step 2 — File structure
Create:
```
docs/
  index.md              # Landing page with a brief intro + table of contents
  getting-started.md    # From zero → first successful action
  features/             # One file per major feature, describing what it is
    <feature>.md
  how-to/               # One file per task, describing how to do it
    <task>.md
  troubleshooting.md    # Common errors, fixes, FAQs
  glossary.md           # Plain-language definitions of app-specific terms
```

### Required frontmatter (every markdown file)

Every file under `docs/` MUST begin with a YAML frontmatter block. The MCP server reads these fields directly to power browse, summary, and synonym-aware search. Treat `aliases` as load-bearing — it is the writer's main lever for catching phrasings that don't match the title.

```yaml
---
id: <category>/<file-basename>            # e.g. how-to/reset-password
title: <human title — same wording as the H1>
category: <getting-started | features | how-to | troubleshooting | glossary | overview>
summary: <≤ 30 words. The pitch. Used by browse + overview tools.>
tags: [<3–6 user-language keywords>]
aliases:                                   # other phrasings users would search for
  - <synonym 1>
  - <synonym 2>
last_updated: YYYY-MM-DD
version: <int, bumped on substantive changes>
---
```

### Heading conventions

Pin every H2's slug on the same line as the heading: `## CSV export {#csv-export}`. Without a pinned slug, the auto-generated slug changes whenever the heading is reworded — breaking any agent or human reference to the section. The slug is part of the section's stable ID; treat it like a URL, not a label.

Each feature / how-to file follows this template:
```markdown
---
id: how-to/<file-basename>
title: <Title phrased as the user would search for it>
category: how-to
summary: <≤ 30 words.>
tags: [<3–6 keywords>]
aliases:
  - <alternate phrasing 1>
  - <alternate phrasing 2>
last_updated: YYYY-MM-DD
version: 1
---

# <Title phrased as the user would search for it>

## What this does {#what-this-does}
<1–3 plain sentences. No jargon.>

## When you'd use it {#when-youd-use-it}
<Concrete situations.>

## Steps {#steps}
1. ...
2. ...
3. ...

## What to expect {#what-to-expect}
<What the user sees when it works.>

## If something goes wrong {#if-something-goes-wrong}
<Issues specific to this feature. Link to troubleshooting.md for general issues.>
```

### Glossary entries

`glossary.md` is special-cased: every H2 is one term. Each entry is short — a 1–3 sentence plain-language definition followed by a single-line HTML comment listing synonyms users might search for instead of the canonical term:

```markdown
## Audience {#audience}

An Audience is a grouped set of users defined by shared traits or behaviour. Audiences power segmentation in campaigns and dashboards.

<!-- aliases: segment, user group, cohort -->
```

The MCP server's glossary tool uses the heading + the `aliases` comment to resolve user phrasings to the canonical term. Skip the aliases line only when the term genuinely has no common synonyms.

## Step 3 — Writing style (non-negotiable)
- **Plain language.** If a sentence has a technical term, replace it or define it inline in 3–6 words.
- **Second person, active voice.** "Click Save" — not "The Save button should be clicked."
- **Short sentences.** One idea per sentence. Aim for ≤20 words.
- **Concrete, not abstract.** "Tap the gear icon in the top right" beats "Navigate to settings."
- **Imperative for steps.** "Open the file" — not "You can open the file."
- **No marketing fluff.** Banned words: powerful, seamless, cutting-edge, revolutionary, leverage, robust, effortless, blazing-fast.
- **Acknowledge limits honestly.** "This only works with PNG files under 5 MB" beats letting the user discover it.
- **Use screenshot placeholders** where a screenshot would help: `![Settings page with the Export button highlighted](TODO/screenshots/export.png)` — leave the TODO so I can fill them in later.

## What to avoid
- Internal architecture, class names, framework details — unless directly visible to the user.
- Code snippets, unless the user is genuinely expected to run code.
- Long option lists without context. Every option needs a one-line "use this when…" hint.
- Burying the action. Lead each how-to with what the user is trying to accomplish, not background.

## Quality bar — apply to every page before moving on
1. Could a first-time user complete the task using only this page?
2. If a single section were retrieved on its own (no surrounding context), would it still answer a real user question?
3. Is anything assumed about what the reader already knows? If yes, fix it.
4. Are headings phrased the way users would actually phrase the question?

## Working process
1. Discovery → output feature inventory → **wait for my confirmation**.
2. Write `docs/index.md` and `docs/getting-started.md` → **pause for review**.
3. After my feedback, generate the rest of the files.
4. Final pass: verify the table of contents in `index.md` matches reality, fix cross-references, and run the quality bar checklist over every page.

If you find anything that's clearly developer-facing rather than user-facing, flag it and skip it — don't include it just because it exists in the code.