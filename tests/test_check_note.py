from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import unittest


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "skills" / "obsidian-summarizer" / "scripts" / "check_note.py"
SCRIPT_DIR = SCRIPT.parent
DEFAULT_PROFILE = ROOT / "skills" / "obsidian-summarizer" / "profiles" / "default.yaml"
sys.path.insert(0, str(SCRIPT_DIR))

from check_note import check_note, load_effective_profile, parse_simple_yaml  # noqa: E402


class CheckNoteTests(unittest.TestCase):
    def write_note(self, directory: str, content: str) -> Path:
        path = Path(directory) / "note.md"
        path.write_text(content, encoding="utf-8")
        return path

    def codes(self, note: Path, profile: dict[str, object] | None = None) -> set[str]:
        return {finding.code for finding in check_note(note, profile)}

    def test_valid_learning_note(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "# Topic\n\n## Common mistakes\n\nNone.\n\n## Glossary\n\nTerm.\n\n"
                "## One-sentence takeaway\n\nDone.\n",
            )
            self.assertEqual(check_note(note, load_effective_profile()), [])

    def test_detects_unclosed_fence_and_missing_image(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(directory, "# Topic\n\n![[assets/missing.png]]\n\n```python\nprint('x')\n")
            codes = self.codes(note)
            self.assertIn("missing-image", codes)
            self.assertIn("unclosed-fence", codes)

    def test_detects_non_english_scripts_in_inline_and_multiline_nested_latex(self):
        samples = {
            "Hebrew": "$\\operatorname{עברית}(x)$",
            "Arabic": "$\\text{العربية}$",
            "Cyrillic": "$$\n\\boxed{\\mathrm{текст}}\n$$",
        }
        with TemporaryDirectory() as directory:
            for name, latex in samples.items():
                with self.subTest(name=name):
                    note = self.write_note(directory, f"# Topic\n\n{latex}\n")
                    self.assertIn("non-english-text-in-latex", self.codes(note))

    def test_english_and_mathematical_unicode_are_allowed_in_latex(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "# Topic\n\n$\\text{expected value}$\n\n$$\n"
                "\\frac{α + β}{2} = ∑_{i=1}^{n} x_i\n$$\n",
            )
            self.assertNotIn("non-english-text-in-latex", self.codes(note))

    def test_non_english_text_outside_math_in_code_is_untouched(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "# Topic\n\n`label = 'עברית'`\n\n```text\nالعربية; [!syntax]\n```\n",
            )
            codes = self.codes(note, {"punctuation.semicolons_in_prose": "forbid"})
            self.assertNotIn("non-english-text-in-latex", codes)
            self.assertNotIn("semicolon-prose", codes)
            self.assertNotIn("invalid-callout", codes)

    def test_latex_inside_callout_is_checked_but_callout_code_is_not(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "> [!note] Math\n> $\\text{עברית}$\n> ```python\n"
                "> token = '[!not-a-callout];'\n> ```\n",
            )
            findings = check_note(note, {"punctuation.semicolons_in_prose": "forbid"})
            codes = {finding.code for finding in findings}
            self.assertIn("non-english-text-in-latex", codes)
            self.assertNotIn("invalid-callout", codes)
            self.assertNotIn("semicolon-prose", codes)

    def test_inline_code_semicolon_is_not_prose(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(directory, "# Topic\n\nUse `for (;;)` to loop.\n")
            self.assertNotIn(
                "semicolon-prose",
                self.codes(note, {"punctuation.semicolons_in_prose": "forbid"}),
            )

    def test_semicolon_in_url_or_entity_is_not_prose(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "# Topic\n\nVisit https://example.test/a;b, [local](docs/a;b), [[a;b]], and render &copy;.\n",
            )
            self.assertNotIn(
                "semicolon-prose",
                self.codes(note, {"punctuation.semicolons_in_prose": "forbid"}),
            )

    def test_frontmatter_is_not_treated_as_prose(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "---\ncssclasses: [wide; compact]\nformula: '$\\text{עברית}$'\n---\n\n# Topic\n",
            )
            codes = self.codes(note, {"punctuation.semicolons_in_prose": "forbid"})
            self.assertNotIn("semicolon-prose", codes)
            self.assertNotIn("non-english-text-in-latex", codes)

    def test_callout_prose_punctuation_is_checked(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(directory, "> [!warning] Read this\n> First clause; second clause — done.\n")
            codes = self.codes(
                note,
                {
                    "punctuation.semicolons_in_prose": "forbid",
                    "punctuation.em_dash": "replace_with_hyphen",
                },
            )
            self.assertTrue({"semicolon-prose", "em-dash"}.issubset(codes))

    def test_highlight_markup_inside_callout_is_an_error(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "> [!important] Practical advice\n> ==Do the simple thing first.==\n",
            )
            findings = [finding for finding in check_note(note) if finding.code == "highlight-in-callout"]
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].level, "error")

    def test_bold_text_inside_callout_is_accepted(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "> [!important] Practical advice\n> **Do the simple thing first.** More context follows.\n",
            )
            self.assertNotIn("highlight-in-callout", self.codes(note))

    def test_highlight_markup_outside_callout_is_accepted(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(directory, "# Topic\n\n==This is the central insight.==\n")
            self.assertNotIn("highlight-in-callout", self.codes(note))

    def test_summary_callout_satisfies_required_takeaway(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "# Topic\n\n## Glossary\n\nTerm.\n\n"
                "> [!summary] One-sentence takeaway\n> **The central insight is concise.**\n",
            )
            profile = load_effective_profile(overrides=["common_mistakes=false"])
            codes = self.codes(note, profile)
            self.assertNotIn("missing-one-sentence-takeaway", codes)
            self.assertNotIn("highlight-in-callout", codes)

    def test_multiline_callout_content_is_checked_for_highlights(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "> [!tip] Connection\n> Ordinary first line.\n> Another line.\n"
                "> The ==important mapping== appears later.\n",
            )
            findings = [finding for finding in check_note(note) if finding.code == "highlight-in-callout"]
            self.assertEqual([finding.line for finding in findings], [4])

    def test_plain_blockquote_highlight_is_not_treated_as_callout(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "> A quoted passage.\n> ==Highlight preserved from the quotation.==\n",
            )
            self.assertNotIn("highlight-in-callout", self.codes(note))

    def test_subheading_for_substantial_common_mistake_remains_valid(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "# Topic\n\n## Common mistakes\n\n"
                "### Retrying a non-idempotent operation\n\n"
                "This misconception needs several paragraphs.\n\n"
                "A developed example and correction follow here.\n",
            )
            profile = load_effective_profile(
                overrides=["glossary=false", "one_sentence_takeaway=false", "common_mistakes=true"]
            )
            self.assertNotIn("missing-common-mistakes", self.codes(note, profile))

    def test_hebrew_flowchart_lr_is_rejected(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(directory, "```mermaid\nflowchart LR\nA[שאילתה] --> B[תגובות]\n```\n")
            self.assertIn("mermaid-direction-mismatch", self.codes(note))

    def test_hebrew_graph_lr_is_rejected(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(directory, "```mermaid\ngraph LR\nA[שאילתה] --> B[תגובות]\n```\n")
            self.assertIn("mermaid-direction-mismatch", self.codes(note))

    def test_hebrew_flowchart_rl_is_accepted(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(directory, "```mermaid\nflowchart RL\nA[שאילתה] --> B[תגובות]\n```\n")
            self.assertNotIn("mermaid-direction-mismatch", self.codes(note))

    def test_hebrew_vertical_flowchart_is_accepted(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(directory, "```mermaid\nflowchart TD\nA[שאילתה] --> B[תגובות]\n```\n")
            codes = self.codes(note)
            self.assertNotIn("mermaid-direction-mismatch", codes)
            self.assertNotIn("mermaid-direction-unverifiable", codes)

    def test_english_flowchart_and_graph_lr_are_accepted(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "```mermaid\nflowchart LR\nA[Fetch comments] --> B[Comments]\n```\n\n"
                "```mermaid\ngraph LR\nA[Request] --> B[Response]\n```\n",
            )
            self.assertNotIn("mermaid-direction-mismatch", self.codes(note))

    def test_english_flowchart_rl_requires_intentional_marker(self):
        with TemporaryDirectory() as directory:
            rejected = self.write_note(
                directory,
                "```mermaid\nflowchart RL\nA[Fetch comments] --> B[Comments]\n```\n",
            )
            self.assertIn("mermaid-direction-mismatch", self.codes(rejected))
            accepted = self.write_note(
                directory,
                "```mermaid\n%% direction: intentional\n"
                "flowchart RL\nA[Newest state] --> B[Earlier state]\n```\n",
            )
            self.assertNotIn("mermaid-direction-mismatch", self.codes(accepted))

    def test_english_vertical_flowchart_is_accepted(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(directory, "```mermaid\nflowchart TD\nA[Request] --> B[Response]\n```\n")
            self.assertNotIn("mermaid-direction-mismatch", self.codes(note))

    def test_diagram_direction_does_not_inherit_note_language(self):
        with TemporaryDirectory() as directory:
            rtl_note = self.write_note(
                directory,
                "# הערה בעברית\n\n```mermaid\nflowchart LR\nA[Request] --> B[Response]\n```\n",
            )
            self.assertNotIn("mermaid-direction-mismatch", self.codes(rtl_note))
            ltr_note = self.write_note(
                directory,
                "# English note\n\n```mermaid\nflowchart RL\nA[שאילתה] --> B[תגובה]\n```\n",
            )
            self.assertNotIn("mermaid-direction-mismatch", self.codes(ltr_note))

    def test_lr_text_outside_mermaid_does_not_trigger(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "The letters LR are ordinary prose.\n\n```text\nflowchart LR\nA[עברית]\n```\n",
            )
            codes = self.codes(note)
            self.assertNotIn("mermaid-direction-mismatch", codes)
            self.assertNotIn("mermaid-direction-unverifiable", codes)

    def test_multiple_mermaid_diagrams_are_checked_independently(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "```mermaid\nflowchart LR\nA[שאילתה] --> B[תגובה]\n```\n\n"
                "```mermaid\nflowchart RL\nA[Request] --> B[Response]\n```\n",
            )
            findings = [
                finding for finding in check_note(note) if finding.code == "mermaid-direction-mismatch"
            ]
            self.assertEqual(len(findings), 2)

    def test_valid_rtl_and_ltr_diagrams_can_coexist(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "```mermaid\nflowchart RL\nA[שאילתה] --> B[תגובה]\n```\n\n"
                "```mermaid\nflowchart LR\nA[Request] --> B[Response]\n```\n",
            )
            codes = self.codes(note)
            self.assertNotIn("mermaid-direction-mismatch", codes)
            self.assertNotIn("mermaid-direction-unverifiable", codes)

    def test_arabic_persian_and_urdu_horizontal_diagrams_are_rtl(self):
        labels = ("العربية", "فارسی", "اردو")
        with TemporaryDirectory() as directory:
            for label in labels:
                with self.subTest(label=label):
                    note = self.write_note(
                        directory,
                        f"```mermaid\nflowchart LR\nA[{label}] --> B[{label}]\n```\n",
                    )
                    self.assertIn("mermaid-direction-mismatch", self.codes(note))

    def test_mixed_language_diagram_uses_dominance_or_explicit_metadata(self):
        with TemporaryDirectory() as directory:
            dominant = self.write_note(
                directory,
                "```mermaid\nflowchart RL\nA[שאילתה query] --> B[תגובות נוספות]\n```\n",
            )
            self.assertNotIn("mermaid-direction-mismatch", self.codes(dominant))
            explicit = self.write_note(
                directory,
                "```mermaid\n%% language: en\nflowchart LR\n"
                "A[שאילתה query] --> B[תגובות response]\n```\n",
            )
            codes = self.codes(explicit)
            self.assertNotIn("mermaid-direction-mismatch", codes)
            self.assertNotIn("mermaid-direction-unverifiable", codes)

    def test_ambiguous_horizontal_diagram_requires_metadata_or_vertical_layout(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(directory, "```mermaid\nflowchart LR\nA --> B\n```\n")
            self.assertIn("mermaid-direction-unverifiable", self.codes(note))

    def test_horizontal_rule_does_not_interfere_with_frontmatter(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "---\ntags: [study]\n---\n\n# Topic\n\nFirst unit.\n\n---\n\n"
                "## Glossary\n\nTerm.\n\n> [!summary] One-sentence takeaway\n"
                "> **The central insight.**\n",
            )
            profile = load_effective_profile(overrides=["common_mistakes=false"])
            self.assertEqual(check_note(note, profile), [])

    def test_code_fence_table_example_is_not_checked(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "# Topic\n\n```markdown\n| A | B |\n|---|---|\n| one | two | three |\n```\n",
            )
            self.assertNotIn("table-width", self.codes(note))

    def test_detects_bad_document_table_width(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(directory, "# Topic\n\n| A | B |\n|---|---|\n| one | two | three |\n")
            self.assertIn("table-width", self.codes(note))

    def test_parses_nested_profile_values_and_inline_lists(self):
        with TemporaryDirectory() as directory:
            profile_path = Path(directory) / "profile.yaml"
            profile_path.write_text(
                "output_language: Hebrew\npunctuation:\n  em_dash: replace_with_hyphen\n"
                'section_headings:\n  Hebrew:\n    glossary: ["מילון", "מושגים"]\n',
                encoding="utf-8",
            )
            profile = parse_simple_yaml(profile_path)
            self.assertEqual(profile["output_language"], "Hebrew")
            self.assertEqual(profile["punctuation.em_dash"], "replace_with_hyphen")
            self.assertEqual(profile["section_headings.Hebrew.glossary"], ["מילון", "מושגים"])

    def test_defaults_profile_merge_and_request_override(self):
        with TemporaryDirectory() as directory:
            selected = Path(directory) / "selected.yaml"
            selected.write_text(
                "output_language: Hebrew\npunctuation:\n  semicolons_in_prose: forbid\n",
                encoding="utf-8",
            )
            effective = load_effective_profile(
                selected,
                ["output_language=Spanish", "glossary=false"],
                DEFAULT_PROFILE,
            )
            self.assertEqual(effective["output_language"], "Spanish")
            self.assertEqual(effective["punctuation.semicolons_in_prose"], "forbid")
            self.assertEqual(effective["punctuation.em_dash"], "replace_with_hyphen")
            self.assertFalse(effective["glossary"])

    def test_cli_without_profile_uses_bundled_defaults(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(directory, "# Topic\n\nText; more text.\n")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(note), "--json"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertIn('"semicolon-prose"', result.stdout)

    def test_unconfigured_language_is_unverifiable_not_missing(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(directory, "# Tema\n\n## Glosario\n\nTérmino.\n")
            profile = load_effective_profile(overrides=["output_language=Spanish"])
            codes = self.codes(note, profile)
            self.assertIn("unverifiable-glossary", codes)
            self.assertNotIn("missing-glossary", codes)
            self.assertNotIn("missing-one-sentence-takeaway", codes)

    def test_configured_additional_language_headings_are_verified(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "# Tema\n\n## Glosario\n\nTérmino.\n\n## Idea central\n\nResultado.\n",
            )
            profile = load_effective_profile(
                overrides=[
                    "output_language=Spanish",
                    'section_headings.Spanish.glossary=["Glosario"]',
                    'section_headings.Spanish.one_sentence_takeaway=["Idea central"]',
                    "common_mistakes=false",
                ]
            )
            codes = self.codes(note, profile)
            self.assertNotIn("missing-glossary", codes)
            self.assertNotIn("unverifiable-glossary", codes)
            self.assertNotIn("missing-one-sentence-takeaway", codes)


if __name__ == "__main__":
    unittest.main()
