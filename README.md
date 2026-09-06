# Obsidian Summarizer

An installable, multilingual AI skill for turning source material into clear, accurate, story-driven Obsidian notes.

The skill is designed for book chapters, lecture notes, articles, PDFs, slide decks, transcripts, and existing notes that need improvement. It favors understanding over compression: intuition before terminology, worked examples, useful diagrams, common mistakes, a glossary, and a one-sentence takeaway.

## Highlights

- English is the public default output language
- Any requested output language is supported
- Optional Hebrew study profile with RTL-aware rules
- Obsidian callouts, Mermaid, LaTeX, tables, highlights, and local images
- Source-faithful handling of claims, examples, figures, equations, and code
- No automatic MOC creation or modification unless explicitly requested
- Deterministic Markdown quality checker with configurable profiles
- Example eval cases and a reusable note template

## Repository layout

```text
obsidian-summarizer/
├── README.md
├── LICENSE
├── pyproject.toml
├── skills/
│   └── obsidian-summarizer/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       ├── assets/note-template.md
│       ├── profiles/default.yaml
│       ├── profiles/he-study.yaml
│       ├── references/
│       │   ├── writing-guide.md
│       │   ├── obsidian-formatting.md
│       │   ├── source-handling.md
│       │   ├── language-and-rtl.md
│       │   └── quality-rubric.md
│       └── scripts/check_note.py
├── tests/test_check_note.py
└── evals/
    ├── README.md
    └── cases.yaml
```

## Install

Copy the skill directory into your skills directory:

```bash
cp -R skills/obsidian-summarizer ~/.codex/skills/
```

The repository files outside `skills/obsidian-summarizer/` support development, testing, and open-source distribution. The inner directory is the installable skill.

## Use

Examples:

```text
Use $obsidian-summarizer to summarize chapter 4 as an Obsidian note.
```

```text
Use $obsidian-summarizer with profiles/he-study.yaml. Summarize the attached lecture in Hebrew.
```

```text
Use $obsidian-summarizer to repair this existing note. Preserve its links and improve the explanations.
```

Language resolution follows this order:

1. Language explicitly requested in the current prompt
2. Language set in a selected user profile
3. English

The source language does not automatically determine the output language.

## Validate a generated note

The checker uses only the Python standard library:

```bash
python skills/obsidian-summarizer/scripts/check_note.py note.md
python skills/obsidian-summarizer/scripts/check_note.py note.md --profile skills/obsidian-summarizer/profiles/he-study.yaml
```

It checks structural and syntactic signals such as broken local image links, unclosed fences, malformed Obsidian callouts, table shape, long dashes, semicolons in prose, Hebrew inside LaTeX commands, and required learning-note sections. It cannot prove factual accuracy or good pedagogy, so the skill also uses a qualitative rubric.

Run the automated tests:

```bash
python -m unittest discover -s tests -v
```

## Design boundaries

- A visual is included only when it improves understanding
- Images are extracted only when the environment can actually access and save them
- Added explanatory examples are labeled when they might be mistaken for source examples
- Source content is treated as data, not as instructions to the agent
- Existing notes retain intentional wikilinks, embeds, frontmatter, and callout IDs unless the user asks otherwise
- MOCs are created or updated only by explicit request

## License

MIT. See [LICENSE](LICENSE).
