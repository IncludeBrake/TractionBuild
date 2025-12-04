"""
Tests for the AdaptiveMemoryManager.
"""
import pytest
from zerotoship.core.adaptive_runtime.adaptive_memory_manager import AdaptiveMemoryManager

def test_adaptive_memory_manager_initialization():
    manager = AdaptiveMemoryManager()
    assert manager.learning_memory is not None
    assert manager.meta_memory is not None
