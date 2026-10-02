---
name: notion-details-summary-blocks
description: How to write <details><summary> Q&A blocks so the Notion markdown converter doesn't mangle them
metadata:
  type: feedback
---

When publishing a lesson's "Check yourself" section to Notion, the `<summary>...</summary>`
question text must be on a single line in the markdown passed to `notion-create-pages` /
`notion-update-page`. A `<summary>` tag whose question text wraps across multiple source
lines (as the `invai-docs/learn/**` markdown files do for readability, e.g. lesson 5.3's
Q1/Q2) gets mis-parsed by the Notion markdown converter: it splits into a broken toggle
with a literal escaped `\<summary\>`/`\</summary\>` visible in the rendered page, and the
real question text gets cut off mid-sentence.

**Why:** Found this by fetching an already-published page (5.3 Label and Profit) and seeing
two of its three `<details>` blocks rendered broken, while the third (whose summary was
already a single line in the source) rendered fine. This was a pre-existing bug in earlier
publishes, not something previously documented.

**How to apply:** Before publishing any lesson with Q&A collapsibles, run a transform that
joins each `<summary>...</summary>` span onto one line (collapse internal newlines to
spaces) before passing content to the Notion tool. A quick python regex:
`re.sub(r'<summary>(.*?)</summary>', lambda m: '<summary>' + re.sub(r'\s+',' ',m.group(1)).strip() + '</summary>', text, flags=re.DOTALL)`.
Also: Notion's enhanced-markdown spec does not document GFM pipe tables (`| a | b |`) —
convert any markdown table to the `<table header-row="true"><tr><td>...` XML block form
before publishing, or it may not render as a table at all.

Also found: the "InvAI Course" parent page's own Course-map table, and the README/Glossary
Notion pages, had drifted stale (still showing modules 03–05 as "Not started" when the
markdown source already marked them Done, and the Glossary page was missing the 03–05
sections entirely). Check these three pages against the current markdown on every run that
adds a module, not just the new lesson pages — the drift is easy to miss since only the
new child pages are obviously "my work."
