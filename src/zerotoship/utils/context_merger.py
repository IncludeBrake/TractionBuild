"""
Utilities for merging contexts from different sources.
"""
from typing import Dict, Any, List

def merge_contexts(base_context: Dict[str, Any], new_contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merges a list of new contexts into a base context.
    A simple "last write wins" strategy is used here.
    """
    merged_context = base_context.copy()
    for ctx in new_contexts:
        merged_context.update(ctx)
    return merged_context
