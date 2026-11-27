# Dividing Doctrines question bank

Start with `index.json`. Its 16 sets follow the project’s guided order. Each file in `sets/` is independently loadable, so a reader can open a category or dimension directly. See `CONVERSION.md` for the source comparison and outstanding decisions.

## Render a set

1. Show `title` and `plainLanguageTitle`. A non-null `featuredQuestionId` can supply a category preview. The preview does not change the first question.
2. Walk `sections` and their `questions` in array order. A section’s `dimensionId` links it to the shared taxonomy. Eschatology has a supplemental Reading Revelation section with a null dimension ID.
3. In guided mode, evaluate `display.guided` first. If it matches, include the question. Otherwise evaluate `display.optional` and offer a matching question by choice. A missing rule is false. Continue in array order after every branch. `recommendWhen` can highlight an already eligible item. Topic exploration can expose additional depth by choice. Apply the edition’s variant selection in both modes.
4. Show the question label from `displayId` when present, falling back to `id`. Display the prompt, any help text, and the choices in order. Store selected choice IDs such as `SAC-03/B`. A single-choice answer has at most one ID. In a multiple-choice answer, a choice marked `exclusive` stands alone. An unanswered item has no selected IDs. An explicit uncertainty response is an answer.
5. After an edit to an earlier answer, reevaluate subsequent eligibility in order. Keep earlier responses available for history, but evaluate guided conditions only against currently applicable responses. Clear dependent confirmations when their underlying answer changes. Keep `asked` history separate from active selections.
6. Use `reviewPriorAnswers` to retrieve potentially relevant earlier answers for review. The response sets can differ across questions. Reuse an answer only when its meaning has been confirmed. Source-authored `routingNotes`, `editorialNotes` and `displayNote` explain cases requiring judgment. Present participant-facing wording from `prompt`, `choices` and `helpText`.

## Evaluate a condition

| Condition | Match |
| --- | --- |
| `true` or `false` | Literal value |
| `selectedAny` | At least one listed choice ID is selected on its question |
| `answered` | The named question has an eligible response |
| `unasked` | The named question has neither been asked nor answered |
| `any`, `all` | At least one child condition matches, or every child matches, respectively |
| `confirmed` | The named clarification has explicitly been confirmed in the current context |
| `variant` | The named group has the specified question selected as its sole formulation |

`validate.py` includes a reference evaluator. The three confirmation keys are `futureTribulationAffirmed` for E7-D, `rationalJustificationNeedsClarification` for P3.1-B/C and `meaningfulCreedSelection` for P5.4. Leave a key unset until its meaning is established. The source documents give no automatic definition of “meaningful” in P5.4. The separate P5.1-A/B/C route into P5.5 remains available.

## Vocabulary and reading

Build one term lookup across every set’s `vocabulary` array. A question can use a term whose primary category is elsewhere. Its `vocabularyLinks` specify a sidebar, an exact inline anchor, or context offered after answering. The vocabulary workbook marks every definition and placement as draft or needing attention. In an editorial preview, keep those statuses visible. The source workbook reserves publication for approved entries. Question-level after-answer links do not classify individual answers.

`vocabulary-sources.json` resolves the source codes at the start of each reference. Other text in a reference specifies a passage or section. Public reading links are included. Internal source documents are identified by title. In Sacramentology, `draftHover` preserves the question bank’s original historical note. The vocabulary link at the same anchor preserves the workbook version. Render at most one annotation at that anchor.

## Edit and validate

Use the category tag and a two-digit number for main question labels. Append a lowercase letter for follow-ups, as in `PRO-01a`. Soteriology uses `SOT-R` for its reconstructed edition. `SAC-11B` identifies an alternate draft. A question’s `id` remains the lookup key for saved answers and routing even when its reviewer label differs.

Keep question, choice and term IDs stable when editing wording or changing display order. The label A, B or C is a separate display field. Give new entries unused IDs. Keep retired IDs reserved. Change a field or rule in the affected set, then run the validator from this directory.

```sh
python -m pip install 'jsonschema>=4.18,<5'
python validate.py
```

The schema uses JSON Schema Draft 2020-12. The validator also checks cross-file IDs, earlier-question references, vocabulary anchors, related sets, draft variants, and source keys.
