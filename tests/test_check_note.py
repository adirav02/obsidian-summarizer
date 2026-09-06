from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest


SCRIPT_DIR = Path(__file__).parents[1] / "skills" / "obsidian-summarizer" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from check_note import check_note, parse_simple_yaml  # noqa: E402


class CheckNoteTests(unittest.TestCase):
    def write_note(self, directory: str, content: str) -> Path:
        path = Path(directory) / "note.md"
        path.write_text(content, encoding="utf-8")
        return path

    def test_valid_learning_note(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(
                directory,
                "# Topic\n\n## Common mistakes\n\nNone.\n\n## Glossary\n\nTerm.\n\n## One-sentence takeaway\n\nDone.\n",
            )
            profile = {"glossary": "true", "one_sentence_takeaway": "true", "common_mistakes": "true"}
            self.assertEqual(check_note(note, profile), [])

    def test_detects_unclosed_fence_and_missing_image(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(directory, "# Topic\n\n![[assets/missing.png]]\n\n```python\nprint('x')\n")
            codes = {finding.code for finding in check_note(note)}
            self.assertIn("missing-image", codes)
            self.assertIn("unclosed-fence", codes)

    def test_profile_punctuation_and_latex(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(directory, "# נושא\n\nטקסט; נוסף — כאן. $\\text{עברית}$\n")
            profile = {
                "punctuation.semicolons_in_prose": "forbid",
                "punctuation.em_dash": "replace_with_hyphen",
            }
            codes = {finding.code for finding in check_note(note, profile)}
            self.assertTrue({"semicolon-prose", "em-dash", "rtl-in-latex-text"}.issubset(codes))

    def test_detects_bad_table_width(self):
        with TemporaryDirectory() as directory:
            note = self.write_note(directory, "# Topic\n\n| A | B |\n|---|---|\n| one | two | three |\n")
            self.assertIn("table-width", {finding.code for finding in check_note(note)})

    def test_parses_nested_profile_values(self):
        with TemporaryDirectory() as directory:
            profile_path = Path(directory) / "profile.yaml"
            profile_path.write_text("output_language: Hebrew\npunctuation:\n  em_dash: replace_with_hyphen\n", encoding="utf-8")
            profile = parse_simple_yaml(profile_path)
            self.assertEqual(profile["output_language"], "Hebrew")
            self.assertEqual(profile["punctuation.em_dash"], "replace_with_hyphen")


if __name__ == "__main__":
    unittest.main()
