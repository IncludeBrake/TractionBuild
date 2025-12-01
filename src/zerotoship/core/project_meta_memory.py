"""
Project Meta Memory System for tractionbuild.
Stores heuristics, failure patterns, and learning from project executions.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Types of memory entries."""
    SUCCESS_PATTERN = "success_pattern"
    FAILURE_PATTERN = "failure_pattern"
    HEURISTIC = "heuristic"
    PERFORMANCE_METRIC = "performance_metric"
    AGENT_BEHAVIOR = "agent_behavior"
    TOKEN_USAGE = "token_usage"
    DRIFT_PATTERN = "drift_pattern"


class MemoryPriority(str, Enum):
    """Priority levels for memory entries."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MemoryEntry:
    """Individual memory entry."""
    id: str
    type: MemoryType
    priority: MemoryPriority
    content: Dict[str, Any]
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    confidence_score: float = 0.0
    tags: Set[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = set()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['tags'] = list(self.tags)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary."""
        data['tags'] = set(data.get('tags', []))
        return cls(**data)


class ProjectMetaMemory(BaseModel):
    """Project meta memory configuration."""
    
    memory_file_path: str = Field(default="data/project_memory.json", description="Memory file path")
    max_entries_per_type: int = Field(default=1000, description="Maximum entries per memory type")
    memory_retention_days: int = Field(default=365, description="Memory retention in days")
    auto_cleanup: bool = Field(default=True, description="Enable automatic memory cleanup")
    backup_enabled: bool = Field(default=True, description="Enable memory backups")


class ProjectMetaMemoryManager:
    """Manages project meta memory for learning and optimization."""
    
    def __init__(self, config: Optional[ProjectMetaMemory] = None):
        """Initialize the memory manager."""
        self.config = config or ProjectMetaMemory()
        self.logger = logging.getLogger(__name__)
        self.memory_file = Path(self.config.memory_file_path)
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self.memory_entries: Dict[str, MemoryEntry] = {}
        self.type_index: Dict[MemoryType, Set[str]] = {}
        self.tag_index: Dict[str, Set[str]] = {}
        
        # Load existing memory
        self._load_memory()
    
    def _load_memory(self):
        """Load memory from file."""
        if not self.memory_file.exists():
            self.logger.info("No existing memory file found. Starting fresh.")
            return
        
        try:
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
            
            # Load entries
            for entry_data in data.get('entries', []):
                entry = MemoryEntry.from_dict(entry_data)
                self.memory_entries[entry.id] = entry
                
                # Update indexes
                if entry.type not in self.type_index:
                    self.type_index[entry.type] = set()
                self.type_index[entry.type].add(entry.id)
                
                for tag in entry.tags:
                    if tag not in self.tag_index:
                        self.tag_index[tag] = set()
                    self.tag_index[tag].add(entry.id)
            
            self.logger.info(f"Loaded {len(self.memory_entries)} memory entries")
            
        except Exception as e:
            self.logger.error(f"Failed to load memory: {str(e)}")
    
    def _save_memory(self):
        """Save memory to file."""
        try:
            data = {
                'entries': [entry.to_dict() for entry in self.memory_entries.values()],
                'metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'total_entries': len(self.memory_entries),
                    'type_counts': {
                        memory_type.value: len(entry_ids)
                        for memory_type, entry_ids in self.type_index.items()
                    }
                }
            }
            
            # Create backup if enabled
            if self.config.backup_enabled and self.memory_file.exists():
                backup_file = self.memory_file.with_suffix('.backup.json')
                try:
                    if backup_file.exists():
                        backup_file.unlink()  # Remove existing backup
                    self.memory_file.rename(backup_file)
                except Exception as e:
                    self.logger.warning(f"Failed to create backup: {str(e)}")
            
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.logger.info(f"Saved {len(self.memory_entries)} memory entries")
            
        except Exception as e:
            self.logger.error(f"Failed to save memory: {str(e)}")
    
    def add_memory_entry(
        self,
        memory_type: MemoryType,
        content: Dict[str, Any],
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        confidence_score: float = 0.5,
        tags: Optional[Set[str]] = None
    ) -> str:
        """
        Add a new memory entry.
        
        Args:
            memory_type: Type of memory entry
            content: Memory content
            priority: Priority level
            confidence_score: Confidence in this memory
            tags: Tags for categorization
            
        Returns:
            Memory entry ID
        """
        entry_id = self._generate_entry_id(memory_type, content)
        now = datetime.now()
        
        entry = MemoryEntry(
            id=entry_id,
            type=memory_type,
            priority=priority,
            content=content,
            created_at=now,
            last_accessed=now,
            confidence_score=confidence_score,
            tags=tags or set()
        )
        
        # Add to memory
        self.memory_entries[entry_id] = entry
        
        # Update indexes
        if memory_type not in self.type_index:
            self.type_index[memory_type] = set()
        self.type_index[memory_type].add(entry_id)
        
        for tag in entry.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = set()
            self.tag_index[tag].add(entry_id)
        
        # Enforce limits
        self._enforce_memory_limits(memory_type)
        
        # Save to disk
        self._save_memory()
        
        self.logger.info(f"Added memory entry {entry_id} of type {memory_type.value}")
        return entry_id
    
    def get_memory_entries(
        self,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[Set[str]] = None,
        priority: Optional[MemoryPriority] = None,
        limit: int = 100
    ) -> List[MemoryEntry]:
        """
        Retrieve memory entries with filters.
        
        Args:
            memory_type: Filter by memory type
            tags: Filter by tags
            priority: Filter by priority
            limit: Maximum number of entries to return
            
        Returns:
            List of matching memory entries
        """
        matching_entries = []
        
        for entry in self.memory_entries.values():
            # Update access count and timestamp
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            
            # Apply filters
            if memory_type and entry.type != memory_type:
                continue
            
            if tags and not entry.tags.intersection(tags):
                continue
            
            if priority and entry.priority != priority:
                continue
            
            matching_entries.append(entry)
        
        # Sort by relevance (confidence * access_count / age)
        matching_entries.sort(
            key=lambda e: (
                e.confidence_score * e.access_count / 
                max(1, (datetime.now() - e.created_at).days)
            ),
            reverse=True
        )
        
        return matching_entries[:limit]
    
    def add_success_pattern(
        self,
        pattern: Dict[str, Any],
        project_id: str,
        agent_id: str,
        confidence_score: float = 0.8
    ) -> str:
        """Add a success pattern to memory."""
        content = {
            'pattern': pattern,
            'project_id': project_id,
            'agent_id': agent_id,
            'context': 'success_pattern'
        }
        
        tags = {f"project:{project_id}", f"agent:{agent_id}", "success"}
        
        return self.add_memory_entry(
            memory_type=MemoryType.SUCCESS_PATTERN,
            content=content,
            priority=MemoryPriority.HIGH,
            confidence_score=confidence_score,
            tags=tags
        )
    
    def add_failure_pattern(
        self,
        pattern: Dict[str, Any],
        project_id: str,
        agent_id: str,
        error_type: str,
        confidence_score: float = 0.7
    ) -> str:
        """Add a failure pattern to memory."""
        content = {
            'pattern': pattern,
            'project_id': project_id,
            'agent_id': agent_id,
            'error_type': error_type,
            'context': 'failure_pattern'
        }
        
        tags = {f"project:{project_id}", f"agent:{agent_id}", "failure", error_type}
        
        return self.add_memory_entry(
            memory_type=MemoryType.FAILURE_PATTERN,
            content=content,
            priority=MemoryPriority.HIGH,
            confidence_score=confidence_score,
            tags=tags
        )
    
    def add_heuristic(
        self,
        heuristic: Dict[str, Any],
        category: str,
        confidence_score: float = 0.6
    ) -> str:
        """Add a heuristic to memory."""
        content = {
            'heuristic': heuristic,
            'category': category,
            'context': 'heuristic'
        }
        
        tags = {f"category:{category}", "heuristic"}
        
        return self.add_memory_entry(
            memory_type=MemoryType.HEURISTIC,
            content=content,
            priority=MemoryPriority.MEDIUM,
            confidence_score=confidence_score,
            tags=tags
        )
    
    def add_performance_metric(
        self,
        metric_name: str,
        value: float,
        context: Dict[str, Any],
        confidence_score: float = 0.9
    ) -> str:
        """Add a performance metric to memory."""
        content = {
            'metric_name': metric_name,
            'value': value,
            'context': context,
            'context_type': 'performance_metric'
        }
        
        tags = {f"metric:{metric_name}", "performance"}
        
        return self.add_memory_entry(
            memory_type=MemoryType.PERFORMANCE_METRIC,
            content=content,
            priority=MemoryPriority.MEDIUM,
            confidence_score=confidence_score,
            tags=tags
        )
    
    def get_relevant_patterns(
        self,
        agent_id: str,
        context: Dict[str, Any],
        pattern_type: str = "both"
    ) -> Dict[str, List[MemoryEntry]]:
        """
        Get relevant patterns for an agent and context.
        
        Args:
            agent_id: Agent identifier
            context: Current context
            pattern_type: "success", "failure", or "both"
            
        Returns:
            Dictionary of relevant patterns
        """
        tags = {f"agent:{agent_id}"}
        
        patterns = {}
        
        if pattern_type in ["success", "both"]:
            success_patterns = self.get_memory_entries(
                memory_type=MemoryType.SUCCESS_PATTERN,
                tags=tags,
                limit=10
            )
            patterns["success"] = success_patterns
        
        if pattern_type in ["failure", "both"]:
            failure_patterns = self.get_memory_entries(
                memory_type=MemoryType.FAILURE_PATTERN,
                tags=tags,
                limit=10
            )
            patterns["failure"] = failure_patterns
        
        return patterns
    
    def get_heuristics(self, category: str, limit: int = 20) -> List[MemoryEntry]:
        """Get heuristics for a specific category."""
        return self.get_memory_entries(
            memory_type=MemoryType.HEURISTIC,
            tags={f"category:{category}"},
            limit=limit
        )
    
    def cleanup_old_memory(self, days: Optional[int] = None) -> int:
        """
        Clean up old memory entries.
        
        Args:
            days: Number of days to keep (uses config default if None)
            
        Returns:
            Number of entries removed
        """
        if days is None:
            days = self.config.memory_retention_days
        
        cutoff_date = datetime.now() - timedelta(days=days)
        removed_count = 0
        
        entries_to_remove = []
        for entry_id, entry in self.memory_entries.items():
            if entry.created_at < cutoff_date:
                entries_to_remove.append(entry_id)
        
        for entry_id in entries_to_remove:
            self._remove_entry(entry_id)
            removed_count += 1
        
        if removed_count > 0:
            self._save_memory()
            self.logger.info(f"Cleaned up {removed_count} old memory entries")
        
        return removed_count
    
    def _generate_entry_id(self, memory_type: MemoryType, content: Dict[str, Any]) -> str:
        """Generate unique entry ID."""
        import hashlib
        
        content_str = json.dumps(content, sort_keys=True)
        timestamp = str(int(datetime.now().timestamp()))
        
        hash_input = f"{memory_type.value}:{content_str}:{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _enforce_memory_limits(self, memory_type: MemoryType):
        """Enforce memory limits for a specific type."""
        if memory_type not in self.type_index:
            return
        
        entry_ids = self.type_index[memory_type]
        if len(entry_ids) <= self.config.max_entries_per_type:
            return
        
        # Remove oldest entries
        entries = [self.memory_entries[entry_id] for entry_id in entry_ids]
        entries.sort(key=lambda e: e.created_at)
        
        entries_to_remove = entries[:-self.config.max_entries_per_type]
        for entry in entries_to_remove:
            self._remove_entry(entry.id)
    
    def _remove_entry(self, entry_id: str):
        """Remove an entry from all indexes."""
        if entry_id not in self.memory_entries:
            return
        
        entry = self.memory_entries[entry_id]
        
        # Remove from main memory
        del self.memory_entries[entry_id]
        
        # Remove from type index
        if entry.type in self.type_index:
            self.type_index[entry.type].discard(entry_id)
        
        # Remove from tag index
        for tag in entry.tags:
            if tag in self.tag_index:
                self.tag_index[tag].discard(entry_id)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            'total_entries': len(self.memory_entries),
            'type_counts': {
                str(memory_type): len(entry_ids)
                for memory_type, entry_ids in self.type_index.items()
            },
            'tag_counts': {
                tag: len(entry_ids)
                for tag, entry_ids in self.tag_index.items()
            },
            'oldest_entry': min(
                (entry.created_at for entry in self.memory_entries.values()),
                default=None
            ),
            'newest_entry': max(
                (entry.created_at for entry in self.memory_entries.values()),
                default=None
            )
        } 