# Annotation and review guidelines

These guidelines define a repeatable human-labeling process for project owners,
annotators, and reviewers. A project-specific schema may add stricter rules, but should
not silently contradict these baseline practices.

## Before labeling

1. Read the project instructions and schema version before opening a task.
2. Confirm the item contains enough information to make a defensible label.
3. Use only labels defined by the active schema. Do not invent synonyms.
4. If an item is ambiguous, incomplete, corrupted, or outside scope, follow the
   project's escalation policy instead of guessing.
5. Do not copy sensitive source content into comments or external tools.

## Produce a useful annotation

- Apply the smallest set of labels that fully represents the evidence.
- Keep the output in the schema's expected structure and data types.
- For classification, choose a label based on the documented decision rule.
- For named-entity tasks, preserve exact text spans and avoid overlapping spans unless
  the schema explicitly permits them.
- For bounding boxes, use the agreed coordinate convention and include the full target
  while minimizing irrelevant background.
- For segmentation, follow the project's pixel/region inclusion rules and document
  uncertain boundaries in the approved review channel.
- Set confidence only when the task schema requests it; confidence is not a substitute
  for following the labeling policy.

## Handle uncertainty and edge cases

Record a concise reason when an approved workflow provides an uncertainty or escalation
field. Distinguish missing evidence from evidence that supports a negative label.
Never infer a person's identity, protected characteristic, or other sensitive attribute
from appearance alone. If a task appears to expose personal or confidential information,
stop and follow the dataset owner's privacy escalation process.

## Review checklist

Reviewers should independently compare the annotation against the source item and
active schema. Check:

- label validity and completeness;
- span, geometry, or structure accuracy where applicable;
- consistency with similar examples and documented edge cases;
- unsupported assumptions and unnecessary sensitive information;
- whether the review decision and comment explain the outcome.

Reject only with a clear, actionable reason. Do not edit an annotator's work silently;
use the documented correction path so the history remains attributable.

## Quality monitoring

Track agreement and error categories by schema version and task type. Use a small,
representative reviewed sample before drawing conclusions about an entire dataset.
Separate guideline defects from individual annotation errors, and revise guidelines
when multiple competent annotators repeatedly interpret a rule differently.

These are operating guidelines, not a claim that the current application automatically
enforces every recommendation. Product features should be marked implemented only after
code and tests verify them.
