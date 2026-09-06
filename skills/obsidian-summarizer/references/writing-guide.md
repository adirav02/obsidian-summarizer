# Writing Guide

## Desired reading experience

Write as a patient expert telling the story of an idea. The reader should feel why the topic exists, see how its pieces connect, and be able to apply or explain it afterward. Avoid a sequence of compressed facts that forces the reader to reconstruct the logic.

## Narrative teaching pattern

Use this pattern when it fits the material:

1. Introduce the problem, tension, or question.
2. Give an intuitive mental model before formal vocabulary.
3. Name and define the idea once the reader has something to attach it to.
4. Develop a concrete example from initial state through result.
5. Explain what the result means and why it matters.
6. Connect the idea to the next concept with an explicit transition.
7. Consolidate the chapter through mistakes, glossary terms, and a takeaway.

Prefer coherent paragraphs for explanation. Use lists for genuine sets, steps, conditions, or comparisons. Do not turn every sentence into a bullet.

## Examples

A useful example has a purpose and an arc:

- State the scenario and inputs
- Walk through the relevant decisions or calculations
- Show the output
- Interpret the output
- State the general lesson

When an example is created for teaching rather than taken from the source, label it as an added or illustrative example if a reader could otherwise attribute it to the author. Do not label ordinary analogies so heavily that the prose becomes awkward.

Prefer one developed example that returns across related concepts over several shallow examples. Use simple numbers and familiar scenarios unless domain realism matters.

## Connections to the user's experience

When reliable conversation context contains a relevant project, implementation, course, previous exercise, or real experience belonging to the user, connect it to the source concept when the mapping materially improves understanding. Prefer a concrete correspondence between what the source explains and something the user actually built, studied, debugged, or designed, and explain why that correspondence is useful.

Present the connection as an applied learning addition rather than an example or claim from the source. A purposeful `tip`, `example`, or `connection` callout may separate it from the source narrative. Never invent project details, constraints, experiences, or results, and do not expose unrelated personal context. Do not force personalization into every note or section, and never let it replace an important source example or explanation. If no reliable and relevant context is available, omit the connection without comment.

## Terminology and depth

Explain a technical term at first meaningful use. Preserve the accepted source or domain term, optionally alongside a translation. Define it again briefly in the glossary for review.

Depth comes from causal explanation, assumptions, edge cases, and worked reasoning. It does not come from repeating the same claim, adding decorative sections, or imposing a minimum word count.

For code, explain the responsibility of the example, the important lines or stages, expected output, and relevant limitation. For equations, explain the symbols, assumptions, and interpretation outside the formula.

## Emphasis and tone

Use `**bold**` selectively to create semantic scan anchors inside coherent narrative paragraphs. Good anchors include an important term at first meaningful use, the decisive part of a definition, a cause-and-effect relationship, an architectural trade-off, an operational consequence, a decision rule, an essential contrast, or a short conclusion embedded in a longer paragraph. The profile value `key_terms_and_scan_anchors` requests this combination of terminology and meaningful argument anchors.

A substantial section should normally reveal enough of its argument through headings, visuals, and emphasized phrases to remain understandable during a quick scan. Account for tables, diagrams, images, headings, and callouts that already provide visual anchors. Do not impose a quota, bold entire paragraphs or every sentence, collect bold fragments in place of prose, or add multiple competing bold spans to a short paragraph. Emphasis must communicate hierarchy rather than decoration.

Reserve `==highlight==` for rare central insights in normal prose outside callouts. If everything is emphasized, nothing is emphasized.

## Common mistakes

Keep one H2 heading for the complete Common Mistakes section in the output language. Present short mistakes as compact bullets with a bold mistake name followed by a concise, self-contained explanation that preserves the qualification and corrective guidance. Do not give every short mistake its own H3 or inflate the table of contents with minor items.

Use an H3 for an individual misconception only when it genuinely needs multiple paragraphs, a developed example, code, an equation, or another substantial explanation. Do not compress a complex misconception until its cause or correction becomes vague. Apply this structural principle in every output language.

Use emojis as navigation cues, especially in section headings or compact labels. Do not place an emoji in every paragraph or decorate serious warnings playfully.

Avoid robotic phrases such as repeated "In summary," canned transitions, and redundant announcements of what the next section will do. Transitions should explain the conceptual relationship.
