# Language and RTL

## Language selection

Load the default profile, deep-merge the selected profile, then apply current-request instructions. The request has highest precedence and English remains the default. Missing mapping fields inherit earlier values, while explicitly supplied leaf values and lists replace earlier ones. Do not automatically mirror the source language.

Write headings, explanations, callout titles, table headers, glossary definitions, captions, and the takeaway in the selected output language. Preserve technical terms in their conventional language when translating them would reduce clarity. At first use, pair a translated term with its accepted English term when helpful.

Do not translate identifiers, API names, commands, filenames, code, mathematical symbols, or quoted UI labels unless the user requests it.

## Translation quality

Translate meaning and teaching flow rather than sentence structure. Prefer natural phrasing in the output language. Preserve qualifications such as "usually," "under these assumptions," and "may" because removing them changes the claim.

When no established translation exists, keep the original term and explain it plainly. Be consistent after choosing a translation.

## RTL notes

For Hebrew, Arabic, Persian, and other RTL output:

- Write natural RTL prose without inserting dummy letters or invisible direction hacks
- Keep code blocks, URLs, paths, commands, identifiers, and formulas unchanged
- Place code and mathematical notation on their own lines when surrounding directionality becomes confusing
- Keep Mermaid syntax left-to-right while allowing readable labels in the output language
- Prefer short table cells when mixing RTL prose with English identifiers
- Put natural-language equation explanations outside math delimiters
- Keep all natural-language text inside inline and display LaTeX in English, regardless of the output language

Do not add HTML direction wrappers unless the user requests them or the target renderer is known to require them. They often make editing harder and reduce portability.

The English-only LaTeX rule applies to every text-bearing command and is not request-overridable in this version. Mathematical symbols, Greek letters, variables, numbers, and LaTeX commands are not natural-language text and remain valid. This is a skill compatibility boundary, not a universal statement about Obsidian renderers.

## Bidirectional clarity

If a sentence begins with an English identifier inside RTL prose and renders ambiguously, rewrite the sentence so it begins naturally in the output language. Do not prefix the line with a meaningless Hebrew character. Use backticks around inline identifiers and isolate long technical strings on their own line.
