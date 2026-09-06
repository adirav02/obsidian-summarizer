# Evaluation plan

These cases test behavior that regex validation cannot establish. Use public-domain, openly licensed, or project-authored fixtures when running them.

For each case, give the evaluator only the request, source fixture, installed skill, and selected profile. Review the output with `references/quality-rubric.md`, then run `scripts/check_note.py` on the Markdown file.

Do not tell the evaluator the expected defects in advance. Record observed failures and make narrow instruction changes supported by those failures.

The initial acceptance target is:

- No checker errors
- No zero in any rubric dimension
- At least 16 out of 20 overall
- No fabricated claims, quotes, page numbers, or asset paths
- Correct language selection and no automatic MOC mutation
