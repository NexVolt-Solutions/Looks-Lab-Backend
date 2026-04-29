from __future__ import annotations

import re
from typing import Any


_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _parse_numeric(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        match = _NUMBER_RE.search(value.replace(",", ""))
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None

    return None


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _health_label_score(label: str) -> float:
    normalized = label.strip().lower()
    if not normalized:
        return 70.0

    if normalized in {"healthy", "strong", "smooth", "bright", "balanced", "clear"}:
        return 90.0
    if normalized in {"normal", "mostly", "moderate", "medium"}:
        return 72.0
    if normalized in {"oily", "dry", "sensitive", "uneven", "rough", "dull", "frizzy"}:
        return 55.0
    if normalized in {"compromised", "weak", "weakened"}:
        return 45.0
    if normalized in {"damaged", "severe"}:
        return 25.0

    if "healthy" in normalized or "smooth" in normalized or "bright" in normalized:
        return 88.0
    if "normal" in normalized or "balanced" in normalized:
        return 75.0
    if "dry" in normalized or "oily" in normalized or "sensitive" in normalized:
        return 58.0
    if "damaged" in normalized or "compromised" in normalized:
        return 35.0

    return 70.0


def _concern_label_score(label: str) -> float:
    normalized = label.strip().lower()
    if not normalized:
        return 70.0

    if normalized in {"none", "no concerns", "normal"}:
        return 90.0
    if normalized in {"low", "mild", "slight"}:
        return 72.0
    if normalized in {"moderate", "visible", "noticeable"}:
        return 55.0
    if normalized in {"high", "severe", "advanced"}:
        return 30.0

    if "none" in normalized or "no concern" in normalized:
        return 90.0
    if "mild" in normalized or "slight" in normalized or "low" in normalized:
        return 72.0
    if "moderate" in normalized or "visible" in normalized or "noticeable" in normalized:
        return 55.0
    if "high" in normalized or "severe" in normalized or "recession" in normalized:
        return 30.0

    return 55.0


def _extract_labeled_scores(values: dict[str, Any], *, concern: bool) -> list[float]:
    scores: list[float] = []
    for value in values.values():
        label = None
        if isinstance(value, dict):
            label = value.get("label")
        elif isinstance(value, str):
            label = value

        if not label:
            continue

        scores.append(_concern_label_score(label) if concern else _health_label_score(label))

    return scores


def _coerce_score(value: Any) -> float | None:
    numeric = _parse_numeric(value)
    if numeric is None:
        return None
    return min(max(float(numeric), 0.0), 100.0)


def extract_domain_score(domain: str, ai_output: dict[str, Any] | None) -> float | None:
    if not ai_output:
        return None

    direct_candidates = [
        ai_output.get("score"),
        ai_output.get("health_score"),
        ai_output.get("overall_score"),
    ]
    for candidate in direct_candidates:
        score = _coerce_score(candidate)
        if score is not None:
            return score

    if domain == "workout":
        attributes = ai_output.get("attributes", {})
        if isinstance(attributes, dict):
            intensity = str(attributes.get("intensity", "")).lower()
            intensity_score_map = {"low": 40.0, "moderate": 65.0, "high": 85.0}
            return intensity_score_map.get(intensity, 60.0)

    if domain == "quit_porn":
        progress = ai_output.get("progress_tracking", {})
        if isinstance(progress, dict):
            return _coerce_score(progress.get("recovery_score")) or 50.0

    if domain == "facial":
        feature_scores = ai_output.get("feature_scores", {})
        if isinstance(feature_scores, dict):
            overall = _coerce_score(feature_scores.get("overall_score"))
            if overall is not None:
                return overall

        progress = ai_output.get("progress_tracking", {})
        if isinstance(progress, dict):
            values = [
                _coerce_score(progress.get("jawline_score")),
                _coerce_score(progress.get("cheekbones_score")),
                _coerce_score(progress.get("symmetry_score")),
            ]
            avg = _average([v for v in values if v is not None])
            if avg is not None:
                return avg

    if domain in {"diet", "height"}:
        progress = ai_output.get("progress_tracking", {})
        if isinstance(progress, dict):
            if domain == "diet":
                values = [
                    _coerce_score(progress.get("consistency")),
                    _coerce_score(progress.get("nutrition_balance")),
                    _coerce_score(progress.get("diet_consistency")),
                ]
            else:
                values = [
                    _coerce_score(progress.get("completion_percent")),
                    _coerce_score(progress.get("consistency")),
                ]
            avg = _average([v for v in values if v is not None])
            if avg is not None:
                return avg

    if domain in {"skincare", "haircare"}:
        health = ai_output.get("health", {})
        concerns = ai_output.get("concerns", {})
        parts: list[float] = []
        if isinstance(health, dict):
            parts.extend(_extract_labeled_scores(health, concern=False))
        if isinstance(concerns, dict):
            parts.extend(_extract_labeled_scores(concerns, concern=True))
        avg = _average(parts)
        if avg is not None:
            return avg

    health = ai_output.get("health", {})
    if isinstance(health, dict):
        overall = _coerce_score(health.get("score") or health.get("health_score") or health.get("overall_score"))
        if overall is not None:
            return overall

    attributes = ai_output.get("attributes", {})
    if isinstance(attributes, dict):
        overall = _coerce_score(attributes.get("overall_score") or attributes.get("score"))
        if overall is not None:
            return overall

    progress = ai_output.get("progress_tracking", {})
    if isinstance(progress, dict):
        for key in (
            "overall_score",
            "score",
            "health_score",
            "recovery_score",
            "consistency",
            "completion_percent",
            "fitness_consistency",
            "diet_consistency",
            "nutrition_balance",
        ):
            overall = _coerce_score(progress.get(key))
            if overall is not None:
                return overall

    return None
