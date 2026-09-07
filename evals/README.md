# Evaluation plan

These cases test behavior that regex validation cannot establish. Use public-domain, openly licensed, or project-authored fixtures when running them.

For each case, give the evaluator only the request, source fixture, installed skill, and selected profile. Review the output with `references/quality-rubric.md`, then run `scripts/check_note.py` on the Markdown file.

Do not tell the evaluator the expected defects in advance. Record observed failures and make narrow instruction changes supported by those failures.

The checked-in `examples/` directory provides full English and Hebrew evidence packages. They are hand-authored reference outputs, not transcripts of an independent skill invocation. Each evaluation states what was actually reviewed and records the checker command and result. Do not claim an Obsidian renderer check unless one was really run.

The initial acceptance target is:

- No checker errors
- No zero in any rubric dimension
- At least 16 out of 20 overall
- No fabricated claims, quotes, page numbers, or asset paths
- Correct language selection and no automatic MOC mutation

## Cross-platform evaluation

Keep live host checks separate from deterministic unit tests. Use the exact shared request in [`portability-prompt.md`](portability-prompt.md), the same source fixture, and the canonical skill or generated bundle as appropriate. Copy [`platform-evaluation-template.md`](platform-evaluation-template.md) for each host/version run.

Collect four distinct kinds of evidence:

1. **Installation test** - Record the resolved path, scope, copy method, and integrity result.
2. **Discovery and activation test** - Record whether the host listed and activated the skill. A known directory alone is not discovery evidence.
3. **Output-quality test** - Review source fidelity and the RTL, Mermaid, LaTeX, callout, wikilink, and embed behavior against the rubric.
4. **Checker test** - Record whether the installed checker actually ran, its exact command, exit status, and findings.

Record the host name and version, model, operating system, and installation mode. Preserve limitations and failures instead of converting them into broad support claims. A manually written reference summary is comparison material, not an independently generated host result.

To exercise the repository's portability mechanics before a live run:

```bash
python -m unittest discover -s tests -v
python scripts/install.py --platform codex --scope project --project-dir /tmp/example --dry-run
python scripts/export_generic_prompt.py --profile skills/obsidian-summarizer/profiles/he-study.yaml --output dist/obsidian-summarizer-he-study-prompt.md --check
```
