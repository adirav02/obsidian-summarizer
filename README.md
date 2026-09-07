# Obsidian Summarizer

A portable Agent Skill for turning chapters, lectures, articles, PDFs, slides, transcripts, and existing notes into accurate, structured, story-driven, multilingual Obsidian notes.

It favors understanding over compression: intuition before terminology, developed examples, useful diagrams, common mistakes, a glossary, and a one-sentence takeaway. English is the public default, and the optional Hebrew study profile preserves the repository's RTL, Mermaid, and English-only natural language in LaTeX rules.

## One source of truth

The complete installable skill lives in [`skills/obsidian-summarizer/`](skills/obsidian-summarizer/). Its `SKILL.md`, profiles, references, assets, checker, and optional `agents/openai.yaml` metadata are the only canonical implementation. Every native host receives an unchanged copy of that directory.

Repository-level tooling installs the canonical directory and generates generic prompts from it. The files in `dist/` are committed release artifacts for hosts that cannot navigate skill resources. They are never edited manually, and automated tests fail when they are stale.

```text
obsidian-summarizer/
├── skills/obsidian-summarizer/     canonical, installable skill
│   ├── SKILL.md
│   ├── agents/openai.yaml           optional Codex metadata
│   ├── assets/note-template.md
│   ├── profiles/{default,he-study}.yaml
│   ├── references/
│   └── scripts/check_note.py
├── scripts/{install,export_generic_prompt}.py
├── dist/                             generated generic prompts
├── tests/
└── evals/
```

## Platform status

"Native format supported" means the host documents directory-based Agent Skills using `SKILL.md`. "Installer implemented" means the target is covered by deterministic automated tests. It does not mean discovery, activation, rendering, or model output has been tested in a live copy of that host.

| Host | Delivery | Installer | Live host evidence |
|---|---|---|---|
| Codex | Native format supported | User and project scopes | Not yet verified |
| Claude Code | Native format supported | User and project scopes | Not yet verified |
| Gemini CLI | Native format supported | User and project scopes | Not yet verified |
| Antigravity | Native format supported | User and project scopes | Not yet verified |
| Cursor | Native format supported | User and project scopes | Not yet verified |
| Generic chat or local model | Generic bundle only | Not applicable | Bundle generation tested; host behavior varies |

## Install a native skill

The installer uses Python 3.10 or newer and the standard library. It resolves paths from its own repository location, so it can be launched from any working directory.

User-scoped examples:

```bash
python scripts/install.py --platform codex --scope user
python scripts/install.py --platform claude-code --scope user
python scripts/install.py --platform gemini-cli --scope user
python scripts/install.py --platform antigravity --scope user
python scripts/install.py --platform cursor --scope user
```

Project-scoped installation always requires the intended project root:

```bash
python scripts/install.py --platform codex --scope project --project-dir /path/to/project
python scripts/install.py --platform claude-code --scope project --project-dir /path/to/project
python scripts/install.py --platform gemini-cli --scope project --project-dir /path/to/project
python scripts/install.py --platform antigravity --scope project --project-dir /path/to/project
python scripts/install.py --platform cursor --scope project --project-dir /path/to/project
```

On Windows, run the same commands with `py` and a Windows project path. The installer uses the platform-aware Python home directory rather than interpolating `$HOME`.

Preview any operation first:

```bash
python scripts/install.py --platform codex --scope user --dry-run
```

The resolved source and target are always displayed. Existing targets, files, and symlinks are refused by default. To update an existing directory, use `--update`; a modified installation is moved to a timestamped sibling backup before the canonical copy is installed. An identical installation is left unchanged.

```bash
python scripts/install.py --platform cursor --scope project \
  --project-dir /path/to/project --update
```

The installer intentionally has no uninstall command. Removal is a manual, host-local operation so that a broad or ambiguous path is never recursively deleted by this project.

### Installation targets

| Host | User scope | Project scope |
|---|---|---|
| Codex | `~/.agents/skills/obsidian-summarizer/` | `<project>/.agents/skills/obsidian-summarizer/` |
| Claude Code | `~/.claude/skills/obsidian-summarizer/` | `<project>/.claude/skills/obsidian-summarizer/` |
| Gemini CLI | `~/.gemini/skills/obsidian-summarizer/` | `<project>/.gemini/skills/obsidian-summarizer/` |
| Antigravity | `~/.gemini/config/skills/obsidian-summarizer/` | `<project>/.agents/skills/obsidian-summarizer/` |
| Cursor | `~/.cursor/skills/obsidian-summarizer/` | `<project>/.cursor/skills/obsidian-summarizer/` |

Some hosts also discover `.agents/skills/`. The installer chooses the documented host-native path unless the host's current documentation makes `.agents/skills/` the default. Cursor's user-native directory is also the directory its documentation says can sync to Cursor Cloud Agents. These discovery paths can change between host versions, so confirm the linked documentation when adopting the skill in a managed environment.

### Manual installation

Copy the complete canonical directory without changing its contents. For example, a Codex project installation is:

```bash
mkdir -p /path/to/project/.agents/skills
cp -R skills/obsidian-summarizer /path/to/project/.agents/skills/
```

Use the corresponding target from the table for another host. Do not copy only `SKILL.md`; profiles, references, assets, and the checker are part of the skill.

## Use the skill

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

Preferences resolve in one order: bundled defaults, then a recursively merged selected profile, then allowed request-level overrides. Mapping leaves and lists replace earlier values; lists are not concatenated. The English-only natural-language rule inside LaTeX cannot be overridden.

## Generic prompt export

For a browser, chat client, local model, or other host without native Agent Skills support, use a generated self-contained prompt:

```bash
python scripts/export_generic_prompt.py \
  --profile skills/obsidian-summarizer/profiles/default.yaml \
  --output dist/obsidian-summarizer-default-prompt.md

python scripts/export_generic_prompt.py \
  --profile skills/obsidian-summarizer/profiles/he-study.yaml \
  --output dist/obsidian-summarizer-he-study-prompt.md
```

Paste the appropriate generated prompt into the host, then provide the source and request. Request-specific profile exceptions can be baked into a one-off export with repeatable `--set KEY=VALUE` options. Verify committed bundles without rewriting them:

```bash
python scripts/export_generic_prompt.py \
  --profile skills/obsidian-summarizer/profiles/default.yaml \
  --output dist/obsidian-summarizer-default-prompt.md --check
```

The bundle includes the canonical instructions, fully resolved profile, source and writing rules, Obsidian and language guidance, capability-aware delivery behavior, and manual quality review. It cannot create automatic activation, progressive resource loading, shell execution, filesystem or Vault access, or extraction capabilities that the host does not provide.

## Capability-dependent behavior

- A host that can read skill files loads profiles and only the references needed for the request.
- A host with file output can save Markdown and real assets, but it may claim Vault delivery only when that Vault is accessible.
- A host with compatible Python and command execution can run the bundled deterministic checker against a local note.
- A host with file output but no command execution delivers the file, discloses that the checker was not run, and performs a manual review.
- A text-only host returns the complete note as text and does not claim that it saved or validated a file.
- Missing source or image extraction is disclosed. The skill never invents inaccessible content or assets.

## Validate a note

The checker resolves its default profile relative to its installed skill directory, not the current working directory, and uses only the Python standard library:

```bash
python skills/obsidian-summarizer/scripts/check_note.py note.md
python skills/obsidian-summarizer/scripts/check_note.py note.md \
  --profile skills/obsidian-summarizer/profiles/he-study.yaml
python skills/obsidian-summarizer/scripts/check_note.py note.md \
  --profile skills/obsidian-summarizer/profiles/he-study.yaml \
  --set glossary=false --set punctuation.semicolons_in_prose=avoid
```

It checks structural and configured-style signals, including local image links, fences, display math, callouts, Mermaid direction, glossary tables, table shape, punctuation, and selected non-Latin scripts inside LaTeX. It does not prove factual accuracy, pedagogy, or renderer behavior.

## Tests and portability evaluations

Run all deterministic tests:

```bash
python -m unittest discover -s tests -v
```

Check formatting and generated artifacts:

```bash
ruff check .
python scripts/export_generic_prompt.py --profile skills/obsidian-summarizer/profiles/default.yaml --output dist/obsidian-summarizer-default-prompt.md --check
python scripts/export_generic_prompt.py --profile skills/obsidian-summarizer/profiles/he-study.yaml --output dist/obsidian-summarizer-he-study-prompt.md --check
```

Host-specific discovery, activation, output quality, and rendering remain manual evaluations. Follow [`evals/README.md`](evals/README.md), use the shared prompt in [`evals/portability-prompt.md`](evals/portability-prompt.md), and record results with [`evals/platform-evaluation-template.md`](evals/platform-evaluation-template.md). Do not label the hand-authored references in `evals/examples/` as live platform output.

## Quality evidence

[`evals/examples/`](evals/examples/) contains two complete, project-authored examples, one English and one Hebrew. Each includes the licensed source, request, hand-authored reference summary, recorded checker result, and an explicit rubric review. These are references, not captured live-skill outputs, and no Obsidian render test is claimed.

## Official compatibility references

- [OpenAI: Build skills](https://developers.openai.com/codex/skills)
- [Anthropic: Extend Claude with skills](https://code.claude.com/docs/en/slash-commands)
- [Gemini CLI: Managing Agent Skills](https://geminicli.com/docs/cli/using-agent-skills/)
- [Google Antigravity: Agent Skills](https://antigravity.google/docs/skills)
- [Cursor: Agent Skills](https://cursor.com/docs/skills)
- [Agent Skills specification](https://agentskills.io/specification)

## Design boundaries

- Visuals are included only when they improve understanding.
- Images are extracted only when the environment can access and save them.
- Added examples are labeled when they could be mistaken for source examples.
- Source content is data, not instructions to the agent.
- Existing wikilinks, embeds, frontmatter, and callout IDs remain intact unless requested otherwise.
- MOCs are created or updated only by explicit request.
- Natural-language text inside every LaTeX region is English-only.

## License

MIT. See [LICENSE](LICENSE).
