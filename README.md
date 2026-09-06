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

1. Load `profiles/default.yaml`
2. Deep-merge a selected profile over the defaults
3. Apply explicit instructions from the current request over both

Nested mappings inherit missing fields and replace explicitly supplied leaves. Lists are replaced, not appended. English is the default output language, and the source language does not determine the summary language.

## Validate a generated note

The checker uses only the Python standard library:

```bash
python skills/obsidian-summarizer/scripts/check_note.py note.md
python skills/obsidian-summarizer/scripts/check_note.py note.md --profile skills/obsidian-summarizer/profiles/he-study.yaml
python skills/obsidian-summarizer/scripts/check_note.py note.md \
  --profile skills/obsidian-summarizer/profiles/he-study.yaml \
  --set glossary=false --set punctuation.semicolons_in_prose=avoid
```

The checker always loads the bundled default profile, even when `--profile` is omitted. A selected profile overlays it, and repeatable `--set KEY=VALUE` options represent request-specific exceptions without changing profile files. Section aliases are configurable under `section_headings.<language>.<section>`; when required aliases are unavailable, the checker reports `unverifiable` information instead of falsely reporting a missing section.

Automated checks cover broken local image links, unclosed fences and display math, malformed Obsidian callout markers, table shape outside code fences, configured punctuation in prose including Callouts, and selected non-Latin linguistic scripts inside inline or display LaTeX. The LaTeX scan crosses lines and nested command content while allowing mathematical Unicode such as Greek symbols. It is intentionally not a Unicode ban or a promise of language identification: Latin-script non-English words, ambiguous Greek text, factual accuracy, pedagogy, renderer behavior, and whether a flexible section structure is appropriate still require qualitative review.

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
- Natural-language text inside any LaTeX region is English-only in this skill version; explanations in other output languages stay outside math delimiters

## Quality evidence

[`evals/examples/`](evals/examples/) contains two complete, project-authored examples, one English and one Hebrew. Each includes the licensed source, request, hand-authored reference summary, recorded checker result, and an explicitly performed rubric review. The records distinguish these references from outputs captured from a live skill invocation and do not claim an Obsidian render test.

## License

MIT. See [LICENSE](LICENSE).
