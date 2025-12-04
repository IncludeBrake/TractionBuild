"""
Adaptive Memory Manager to unify LearningMemory and ProjectMetaMemory.
"""
from ..learning_memory import LearningMemory
from ..project_meta_memory import ProjectMetaMemoryManager

class AdaptiveMemoryManager:
    def __init__(self):
        self.learning_memory = LearningMemory()
        self.meta_memory = ProjectMetaMemoryManager()

    def retrieve(self, query: str):
        """Return merged context from both memories."""
        meta = self.meta_memory.query(query)
        learn = self.learning_memory.query(query)
        return {**learn, **meta} if meta or learn else {}

    def record_outcome(self, context: dict):
        """Persist crew outcome into both memories."""
        self.meta_memory.store(context)
        self.learning_memory.add(context)
    # I will add more logic here later to combine the two memories.
