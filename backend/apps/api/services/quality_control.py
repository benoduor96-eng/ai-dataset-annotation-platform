"""Schema-aware annotation quality checks for common labeling tasks.

The checks are intentionally deterministic and side-effect free. They return
machine-readable issue codes so the API and future review tooling can present
consistent feedback without rewriting submitted annotation data.
"""
from math import isfinite
from collections.abc import Mapping


def _label_names(schema):
    names = set()
    for item in schema.labels or []:
        if isinstance(item, str):
            name = item.strip()
        elif isinstance(item, Mapping):
            name = str(item.get("name", "")).strip()
        else:
            continue
        if name:
            names.add(name.casefold())
    return names


def _issue(code, path, message):
    return {"code": code, "path": path, "message": message}


def _check_label(value, allowed, path, issues):
    if not isinstance(value, str) or not value.strip():
        issues.append(_issue("label_required", path, "A non-empty label is required."))
    elif allowed and value.casefold() not in allowed:
        issues.append(_issue("unknown_label", path, "Label is not defined by the annotation schema."))


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def validate_annotation_data(*, data, schema, task_payload=None):
    """Validate annotation JSON against a schema's label type.

    Supported canonical payload shapes:
    - classification: {"label": "cat"}
    - ner: {"entities": [{"start": 0, "end": 3, "text": "cat", "label": "ANIMAL"}]}
    - bbox: {"boxes": [{"x_min": 1, "y_min": 2, "x_max": 10, "y_max": 12, "label": "car"}]}
    - segmentation: {"segments": [{"label": "road", "points": [[0, 0], [1, 0], [1, 1]]}]}

    Coordinates may be pixel or normalized values; the validator checks their
    structure and ordering rather than assuming an image size or coordinate scale.
    """
    issues = []
    if not isinstance(data, Mapping):
        return [_issue("annotation_object_required", "$", "Annotation data must be a JSON object.")]

    allowed = _label_names(schema)
    label_type = schema.label_type

    if label_type == "classification":
        _check_label(data.get("label"), allowed, "$.label", issues)

    elif label_type == "ner":
        entities = data.get("entities")
        if not isinstance(entities, list):
            return [_issue("entities_required", "$.entities", "NER data must contain an entities list.")]
        text = (task_payload or {}).get("text")
        text_length = len(text) if isinstance(text, str) else None
        for index, entity in enumerate(entities):
            path = f"$.entities[{index}]"
            if not isinstance(entity, Mapping):
                issues.append(_issue("entity_object_required", path, "Each entity must be an object."))
                continue
            start, end = entity.get("start"), entity.get("end")
            if not isinstance(start, int) or isinstance(start, bool) or not isinstance(end, int) or isinstance(end, bool):
                issues.append(_issue("span_integer_required", path, "Entity start and end must be integers."))
            elif start < 0 or start >= end or (text_length is not None and end > text_length):
                issues.append(_issue("span_out_of_range", path, "Entity span must satisfy 0 <= start < end and fit the source text."))
            _check_label(entity.get("label"), allowed, f"{path}.label", issues)
            entity_text = entity.get("text")
            if entity_text is not None and not isinstance(entity_text, str):
                issues.append(_issue("entity_text_invalid", f"{path}.text", "Entity text must be a string when provided."))

    elif label_type == "bbox":
        boxes = data.get("boxes")
        if not isinstance(boxes, list):
            return [_issue("boxes_required", "$.boxes", "Bounding-box data must contain a boxes list.")]
        for index, box in enumerate(boxes):
            path = f"$.boxes[{index}]"
            if not isinstance(box, Mapping):
                issues.append(_issue("box_object_required", path, "Each box must be an object."))
                continue
            _check_label(box.get("label"), allowed, f"{path}.label", issues)
            coordinates = [box.get(key) for key in ("x_min", "y_min", "x_max", "y_max")]
            if not all(_number(value) for value in coordinates):
                issues.append(_issue("box_coordinates_invalid", path, "Box coordinates must be finite numbers."))
            elif coordinates[0] >= coordinates[2] or coordinates[1] >= coordinates[3]:
                issues.append(_issue("box_dimensions_invalid", path, "Maximum coordinates must be greater than minimum coordinates."))

    elif label_type == "segmentation":
        segments = data.get("segments")
        if not isinstance(segments, list):
            return [_issue("segments_required", "$.segments", "Segmentation data must contain a segments list.")]
        for index, segment in enumerate(segments):
            path = f"$.segments[{index}]"
            if not isinstance(segment, Mapping):
                issues.append(_issue("segment_object_required", path, "Each segment must be an object."))
                continue
            _check_label(segment.get("label"), allowed, f"{path}.label", issues)
            points = segment.get("points")
            if not isinstance(points, list) or len(points) < 3:
                issues.append(_issue("polygon_points_required", f"{path}.points", "A polygon requires at least three points."))
                continue
            for point_index, point in enumerate(points):
                point_path = f"{path}.points[{point_index}]"
                if not isinstance(point, (list, tuple)) or len(point) != 2 or not all(_number(value) for value in point):
                    issues.append(_issue("point_coordinates_invalid", point_path, "Each point must contain two finite numeric coordinates."))

    else:
        issues.append(_issue("unsupported_schema_type", "$", "This annotation schema type is not supported by quality checks."))

    return issues


def build_quality_report(*, annotations, schema, task_payload=None):
    """Return a stable aggregate report for a collection of annotation records."""
    results = []
    for annotation in annotations:
        issues = validate_annotation_data(
            data=annotation.data,
            schema=schema,
            task_payload=task_payload,
        )
        results.append({
            "annotation_id": annotation.pk,
            "annotator_id": annotation.annotator_id,
            "valid": not issues,
            "issue_count": len(issues),
            "issues": issues,
        })
    total = len(results)
    valid_count = sum(1 for result in results if result["valid"])
    return {
        "schema_id": schema.pk,
        "schema_version": schema.version,
        "annotation_count": total,
        "valid_count": valid_count,
        "invalid_count": total - valid_count,
        "validity_rate": round(valid_count / total, 4) if total else None,
        "results": results,
    }
