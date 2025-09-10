"""
Anti-hallucination guardrails for SMM outputs.
Ensures consistency and reliability of generated market analysis.
"""

from src.tractionbuild.core.types import CrewResult
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any
import json

def check_consistency(result: CrewResult) -> CrewResult:
    """
    Check internal consistency of SMM results using semantic similarity.
    Flags potential hallucinations or inconsistencies.
    """
    if not result.artifacts:
        result.warnings.append("No artifacts generated; cannot check consistency")
        return result

    try:
        model = SentenceTransformer("all-MiniLM-L6-v2")

        # Extract text content from artifacts
        text_contents = []
        for artifact in result.artifacts:
            if artifact.data:
                if isinstance(artifact.data, str):
                    text_contents.append(artifact.data)
                elif isinstance(artifact.data, dict):
                    # Convert dict to string representation
                    text_contents.append(json.dumps(artifact.data, sort_keys=True))
                elif isinstance(artifact.data, list):
                    # Convert list to string representation
                    text_contents.append(json.dumps(artifact.data, sort_keys=True))

        if len(text_contents) < 2:
            result.warnings.append("Insufficient artifacts for consistency check")
            return result

        # Generate embeddings
        embeddings = [model.encode(text) for text in text_contents]

        # Calculate pairwise similarities
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                similarity = np.dot(embeddings[i], embeddings[j]) / (
                    np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                )
                similarities.append(similarity)

        if not similarities:
            return result

        # Analyze similarity distribution
        avg_similarity = np.mean(similarities)
        min_similarity = np.min(similarities)
        max_similarity = np.max(similarities)

        # Flag potential inconsistencies
        if avg_similarity < 0.3:
            result.warnings.append(".2f")
        elif min_similarity < 0.1:
            result.warnings.append(".2f")
        elif max_similarity < 0.5:
            result.warnings.append(".2f")
        # Check for contradictory information
        if _detect_contradictions(text_contents):
            result.warnings.append("Potential contradictory information detected in artifacts")

        # Update result metadata with consistency metrics
        result.stats.update({
            "consistency_avg_similarity": float(avg_similarity),
            "consistency_min_similarity": float(min_similarity),
            "consistency_max_similarity": float(max_similarity)
        })

    except Exception as e:
        result.warnings.append(f"Consistency check failed: {str(e)}")

    return result

def _detect_contradictions(text_contents: List[str]) -> bool:
    """
    Simple contradiction detection based on keyword analysis.
    Returns True if potential contradictions are detected.
    """
    contradictions = [
        (["free", "premium"], ["expensive", "paid"]),
        (["easy", "simple"], ["complex", "difficult"]),
        (["fast", "quick"], ["slow", "time-consuming"]),
        (["reliable", "stable"], ["unreliable", "buggy"])
    ]

    for content in text_contents:
        content_lower = content.lower()
        for pos_group, neg_group in contradictions:
            pos_count = sum(1 for word in pos_group if word in content_lower)
            neg_count = sum(1 for word in neg_group if word in content_lower)

            if pos_count > 0 and neg_count > 0:
                return True

    return False

def validate_confidence_scores(result: CrewResult, min_threshold: float = 0.3) -> CrewResult:
    """Validate that confidence scores meet minimum thresholds."""
    low_confidence_artifacts = []

    for i, artifact in enumerate(result.artifacts):
        confidence = artifact.meta.get("confidence", 0.5)
        if confidence < min_threshold:
            low_confidence_artifacts.append(f"Artifact {i} ({artifact.type}): {confidence:.2%}")

    if low_confidence_artifacts:
        result.warnings.append(
            f"Low confidence scores detected: {', '.join(low_confidence_artifacts)}. "
            "Consider regenerating or manual review."
        )

    return result

def cross_reference_validation(result: CrewResult) -> CrewResult:
    """Cross-reference generated data against known patterns."""
    # This would integrate with external validation services
    # For now, just check for basic data completeness

    required_sections = ["avatars", "competitors", "channels", "hooks"]
    found_sections = set()

    for artifact in result.artifacts:
        if artifact.type == "json" and isinstance(artifact.data, dict):
            found_sections.update(artifact.data.keys())

    missing_sections = set(required_sections) - found_sections
    if missing_sections:
        result.warnings.append(f"Missing analysis sections: {', '.join(missing_sections)}")

    return result

def comprehensive_guardrail_check(result: CrewResult) -> CrewResult:
    """Run all guardrail checks on SMM results."""
    result = check_consistency(result)
    result = validate_confidence_scores(result)
    result = cross_reference_validation(result)

    # Add overall quality score
    warning_count = len(result.warnings)
    quality_score = max(0.0, 1.0 - (warning_count * 0.1))

    result.stats["quality_score"] = quality_score

    if quality_score < 0.7:
        result.warnings.append(".1f")
    return result
