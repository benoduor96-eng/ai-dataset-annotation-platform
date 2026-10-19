"""Lightweight, deterministic inter-annotator agreement metrics."""
from __future__ import annotations

import json
from collections import defaultdict
from itertools import combinations

from apps.annotations.models import Annotation


def _canonical(value) -> str:
    """Normalize JSON-compatible annotation data for exact-match comparison."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def project_agreement(project) -> dict:
    """Calculate exact-match agreement for tasks labeled by distinct annotators.

    Each task contributes all pairs of annotations made by different annotators.
    Tasks with fewer than two distinct annotators are excluded. This is a simple
    exact-match quality signal, not a substitute for Cohen's kappa or domain review.
    """
    grouped = defaultdict(list)
    annotations = Annotation.objects.filter(
        task__dataset__project=project
    ).select_related("task").order_by("task_id", "created_at", "pk")

    for annotation in annotations:
        grouped[annotation.task_id].append(
            (annotation.annotator_id, _canonical(annotation.data))
        )

    compared_tasks = 0
    pairwise_comparisons = 0
    matching_pairs = 0
    multi_annotated_tasks = 0

    for entries in grouped.values():
        annotators = {annotator_id for annotator_id, _ in entries}
        if len(annotators) < 2:
            continue
        multi_annotated_tasks += 1
        task_pairs = [
            (left, right)
            for left, right in combinations(entries, 2)
            if left[0] != right[0]
        ]
        if not task_pairs:
            continue
        compared_tasks += 1
        pairwise_comparisons += len(task_pairs)
        matching_pairs += sum(left[1] == right[1] for left, right in task_pairs)

    return {
        "multi_annotated_task_count": multi_annotated_tasks,
        "agreement_task_count": compared_tasks,
        "pairwise_comparisons": pairwise_comparisons,
        "exact_match_agreement": (
            round(matching_pairs / pairwise_comparisons, 4)
            if pairwise_comparisons else None
        ),
    }
