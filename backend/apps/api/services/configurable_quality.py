"""Apply configurable quality gates to schema-validation reports."""
from copy import deepcopy

def apply_quality_rules(report, annotations, rules):
    result = deepcopy(report)
    active = [rule for rule in rules if rule.enabled]
    rows = {row["annotation_id"]: row for row in result["results"]}
    for rule in active:
        params = rule.parameters or {}
        if rule.rule_type == "max_annotations" and len(annotations) > params.get("maximum", 1):
            maximum = params.get("maximum", 1)
            for annotation in annotations[maximum:]:
                if annotation.pk in rows:
                    rows[annotation.pk]["issues"].append({"code": "max_annotations_exceeded", "path": "$", "message": f"Rule '{rule.name}' allows at most {maximum} annotations per task."})
        for annotation in annotations:
            row = rows.get(annotation.pk)
            if row is None:
                continue
            issue = None
            if rule.rule_type == "min_confidence":
                minimum = params.get("minimum", 0.0)
                if annotation.confidence is None or annotation.confidence < minimum:
                    issue = {"code": "confidence_below_minimum", "path": "$.confidence", "message": f"Rule '{rule.name}' requires confidence >= {minimum}."}
            elif rule.rule_type == "require_non_empty" and not annotation.data:
                issue = {"code": "annotation_empty", "path": "$", "message": f"Rule '{rule.name}' requires non-empty annotation data."}
            elif rule.rule_type == "allowed_labels":
                allowed = {x.casefold() for x in params.get("labels", [])}
                data = annotation.data if isinstance(annotation.data, dict) else {}
                labels = [data["label"]] if isinstance(data.get("label"), str) else []
                for key in ("entities", "boxes", "segments"):
                    items = data.get(key, [])
                    if isinstance(items, list):
                        labels.extend(item["label"] for item in items if isinstance(item, dict) and isinstance(item.get("label"), str))
                if any(label.casefold() not in allowed for label in labels):
                    issue = {"code": "configured_label_not_allowed", "path": "$", "message": f"Rule '{rule.name}' contains a label outside its allow-list."}
            if issue:
                row["issues"].append(issue)
    for row in result["results"]:
        row["issue_count"] = len(row["issues"])
        row["valid"] = row["issue_count"] == 0
    total = len(result["results"])
    valid = sum(1 for row in result["results"] if row["valid"])
    result.update({"valid_count": valid, "invalid_count": total-valid, "validity_rate": round(valid/total, 4) if total else None,
                   "applied_rules": [{"id": r.pk, "name": r.name, "rule_type": r.rule_type} for r in active]})
    return result
