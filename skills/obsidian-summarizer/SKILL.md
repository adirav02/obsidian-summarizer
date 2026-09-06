---
name: obsidian-summarizer
description: Create or improve learning-focused Obsidian Markdown notes from chapters, lectures, articles, PDFs, slides, transcripts, or existing notes. Use when the user wants an accurate, engaging summary with explanations, examples, and Obsidian-native formatting. Do not use for ordinary short summaries that are not intended as Obsidian notes.
metadata:
  short-description: Create rich learning notes for Obsidian
---

# Obsidian Summarizer

Turn source material into a self-contained Obsidian note that helps the reader understand and remember the material. Optimize for comprehension and source fidelity, not maximum compression or decorative formatting.

## Resolve the request

Determine the source scope, desired depth, note purpose, and output language from the current request. Ask only when missing information would materially change the result.

Always load and resolve preferences in this order:

1. Load [profiles/default.yaml](profiles/default.yaml).
2. Deep-merge a user-selected profile over those defaults.
3. Apply explicit instructions in the current request over both profiles.

Merge mappings recursively. A value supplied at a leaf replaces the earlier value; an omitted field inherits the earlier value. Lists replace earlier lists rather than being appended. English remains the default `output_language`. Do not infer output language from the source language. Treat style values such as `auto`, `adaptive`, and `when_useful` as decision policies, not literal output.

If the user selects a profile, read it before drafting. The bundled profiles are:

- [profiles/default.yaml](profiles/default.yaml) for public defaults
- [profiles/he-study.yaml](profiles/he-study.yaml) for Adir's Hebrew study-note preferences

Keep the effective preferences used for drafting available for validation. When running the checker, pass the selected profile with `--profile` and represent current-request exceptions with repeatable `--set KEY=VALUE` arguments. Do not edit the default profile to encode a one-off request.

## Load only relevant guidance

- Always read [references/writing-guide.md](references/writing-guide.md) and [references/source-handling.md](references/source-handling.md).
- Read [references/obsidian-formatting.md](references/obsidian-formatting.md) when producing or repairing Markdown formatting, visuals, equations, callouts, tables, or images.
- Read [references/language-and-rtl.md](references/language-and-rtl.md) for non-English output, translation, bidirectional text, or any RTL language.
- Read [references/quality-rubric.md](references/quality-rubric.md) before the final review of a substantial note.

## Work from a source map

Before drafting, identify the source's major ideas, explanatory sequence, definitions, examples, equations, code, figures, qualifications, and conclusions. Use that map to prevent omissions and to distinguish central ideas from supporting detail.

Build a teaching sequence rather than mechanically following headings when reordering improves understanding and does not distort the source. Establish the motivating problem, develop intuition, introduce formal terminology, work through examples, connect ideas, then consolidate learning.

## Write the note

Use the source map and selected profile. A substantial learning note normally includes:

- A clear title and short orientation
- A narrative explanation organized into meaningful sections
- Developed examples where they materially improve understanding
- Visuals, equations, code, tables, highlights, and callouts only when useful
- Common mistakes or misconceptions when the topic has plausible traps
- A glossary of important terms
- A one-sentence chapter or note takeaway

This is a flexible teaching structure, not a mandatory heading template. For short material, omit sections that would be empty or artificial. Do not pad the note to hit a word count.

Do not create or update a MOC unless the user explicitly asks. Do not silently alter unrelated notes or vault configuration.

## Keep natural language in LaTeX English-only

Inside every inline or display LaTeX region, natural-language text must be English. This applies to every command that can contain text, not only `\text{...}`, and cannot be overridden by a request or renderer capability in this version of the skill. Put explanations in the note's output language outside the math delimiters.

Mathematical symbols, Greek letters, variables, numbers, and valid LaTeX commands remain allowed. This compatibility constraint is specific to the skill; it is not a claim that every Obsidian installation fails to render other languages in math.

## Handle assets honestly

When figures from the source materially aid understanding and the environment supports extraction, save them beside the note or in the user's requested assets folder and use relative Obsidian embeds. Add a caption or nearby explanation telling the reader what to notice.

If extraction is unavailable or unreliable, explain the missing asset or use a text-native alternative such as Mermaid. Never invent a filename, image, page reference, quotation, or source claim.

## Review and deliver

Check the note against the source map and the quality rubric. Verify that diagrams, equations, tables, links, code fences, and callouts are syntactically plausible. Run `scripts/check_note.py` when a local Markdown file exists. Fix errors and review warnings with judgment. The checker supports structure but does not establish factual accuracy or pedagogical quality.

Deliver the Markdown file and any real local assets. Briefly disclose unreadable or unavailable source portions and any important limitations.
