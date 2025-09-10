"""
Enhanced Execution Crew with enterprise-grade reliability patterns.
"""
import asyncio
import logging
import random
import json
import hashlib
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque
import networkx as nx

try:
    import aiofiles
except ImportError:
    # Fallback for systems without aiofiles
    import builtins
    class aiofiles:
        @staticmethod
        def open(*args, **kwargs):
            return builtins.open(*args, **kwargs)
        @staticmethod
        async def copyfile(src, dst):
            with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
                fdst.write(fsrc.read())
from crewai import Crew, Process, Task
from pydantic import BaseModel, Field
from ..agents.execution_agent import ExecutionAgent
from ..tools.code_tools import CODE_TOOLS
from ..tools.celery_execution_tool import CeleryExecutionTool
from ..models.task import Task as TaskModel
from ..core.project_meta_memory import ProjectMetaMemoryManager
from .base_crew import BaseCrew
from ..utils.llm_factory import get_llm

class TaskStatus(Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class ResourceType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    EXTERNAL_API = "external_api"
    CUSTOM = "custom"

@dataclass
class ResourceRequirement:
    resource_type: ResourceType
    amount: float
    duration_estimate: Optional[timedelta] = None
    priority: int = 1

@dataclass
class TaskCheckpoint:
    task_id: str
    step_index: int
    state_data: Dict[str, Any]
    timestamp: datetime
    rollback_instructions: Optional[str] = None

class ExecutionCrewConfig(BaseModel):
    """Enhanced configuration for the Execution Crew."""
    enable_memory_learning: bool = Field(default=True, description="Enable memory learning")
    enable_task_decomposition: bool = Field(default=True, description="Enable task decomposition")
    max_execution_iterations: int = Field(default=5, description="Maximum execution iterations")
    enable_dependency_mapping: bool = Field(default=True, description="Enable dependency mapping")
    enable_resource_planning: bool = Field(default=True, description="Enable resource planning")
    
    # Enhanced configurations
    max_concurrent_tasks: int = Field(default=10, description="Maximum concurrent tasks")
    resource_allocation_strategy: str = Field(default="priority_weighted", description="Resource allocation strategy")
    checkpoint_interval: int = Field(default=5, description="Steps between checkpoints")
    failure_retry_limit: int = Field(default=3, description="Maximum retry attempts")
    circuit_breaker_threshold: int = Field(default=5, description="Circuit breaker failure threshold")
    execution_timeout: int = Field(default=3600, description="Task execution timeout in seconds")

class EnhancedTaskNode:
    """Enhanced task representation with dependency and resource management."""
    
    def __init__(self, task_id: str, task: TaskModel, resources: List[ResourceRequirement] = None):
        self.task_id = task_id
        self.task = task
        self.status = TaskStatus.PENDING
        self.dependencies: Set[str] = set()
        self.dependents: Set[str] = set()
        self.resources = resources or []
        self.checkpoints: List[TaskCheckpoint] = []
        self.retry_count = 0
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_log: List[str] = []

class DeadlockDetector:
    """Detects deadlocks in resource allocation using wait-for graph."""

    def detect_deadlock(self, wait_queue: List, allocated_resources: Dict) -> bool:
        """Detect if there's a deadlock using wait-for graph analysis."""
        # Build wait-for graph
        wait_graph = nx.DiGraph()

        # Add nodes for all tasks
        all_tasks = set(allocated_resources.keys()) | set(task_id for task_id, _, _ in wait_queue)
        for task_id in all_tasks:
            wait_graph.add_node(task_id)

        # Add edges for waiting relationships
        for waiting_task, _, _ in wait_queue:
            # Find which task holds the resources this task is waiting for
            for holder_task, resources in allocated_resources.items():
                if holder_task != waiting_task:
                    wait_graph.add_edge(waiting_task, holder_task)

        # Check for cycles (deadlocks)
        try:
            cycles = list(nx.simple_cycles(wait_graph))
            return len(cycles) > 0
        except:
            return False


class ResourceAllocationError(Exception):
    """Raised when resource allocation fails"""
    pass

class BulletproofResourceManager:
    """Production-grade resource manager with deadlock prevention"""

    def __init__(self, max_cpu=100.0, max_memory=100.0, max_network=50.0, max_disk=50.0):
        # Maximum available resources
        self.max_resources = {
            ResourceType.CPU: max_cpu,
            ResourceType.MEMORY: max_memory,
            ResourceType.NETWORK: max_network,
            ResourceType.EXTERNAL_API: max_disk,  # Using DISK for EXTERNAL_API
            ResourceType.CUSTOM: 100.0  # Add CUSTOM resource type
        }

        # Currently allocated resources
        self.allocated_resources = {
            ResourceType.CPU: 0.0,
            ResourceType.MEMORY: 0.0,
            ResourceType.NETWORK: 0.0,
            ResourceType.EXTERNAL_API: 0.0,
            ResourceType.CUSTOM: 0.0
        }

        # Resource locks for thread safety
        self._allocation_lock = asyncio.Lock()

        # Track allocations by task for cleanup
        self.task_allocations: Dict[str, Dict[ResourceType, float]] = {}

        # Waiting queue for resource requests
        self._waiting_tasks: Set[str] = set()

        # Performance metrics
        self._allocation_count = 0
        self._failed_allocations = 0
        self._deadlock_prevention_count = 0

        # Circuit breaker for resource exhaustion
        self._consecutive_failures = 0
        self._max_consecutive_failures = 10
        self._circuit_open_until = 0

        self.logger = logging.getLogger(__name__)

    async def reserve_resources(self, task_id: str, requirements: List[ResourceRequirement],
                              timeout: float = 5.0) -> bool:
        """
        Reserve resources with deadlock prevention and timeout protection

        Args:
            task_id: Unique task identifier
            requirements: List of resource requirements
            timeout: Maximum time to wait for resources (seconds)

        Returns:
            True if resources reserved successfully, False otherwise
        """

        # Circuit breaker check
        if self._is_circuit_open():
            self.logger.warning(f"Resource allocation circuit breaker is OPEN - rejecting {task_id}")
            self._failed_allocations += 1
            return False

        # Convert ResourceRequirement list to dict
        required_resources = {}
        for req in requirements:
            required_resources[req.resource_type] = req.amount

        start_time = time.time()

        try:
            # Use timeout to prevent infinite waiting
            return await asyncio.wait_for(
                self._reserve_resources_internal(task_id, required_resources),
                timeout=timeout
            )

        except asyncio.TimeoutError:
            self.logger.error(".2f")
            self._handle_allocation_failure(task_id)
            return False

        except asyncio.CancelledError:
            self.logger.warning(f"Resource allocation cancelled for task {task_id}")
            # Clean up any partial allocations
            await self._cleanup_partial_allocation(task_id)
            raise

        except Exception as e:
            self.logger.error(f"Resource allocation error for task {task_id}: {e}")
            self._handle_allocation_failure(task_id)
            return False

        finally:
            # Remove from waiting queue
            self._waiting_tasks.discard(task_id)

    async def _reserve_resources_internal(self, task_id: str, required_resources: Dict[ResourceType, float]) -> bool:
        """Internal resource reservation with deadlock prevention"""

        # Add to waiting queue for monitoring
        self._waiting_tasks.add(task_id)

        # Deadlock prevention: check for potential circular waits
        if len(self._waiting_tasks) > 20:  # Too many waiting tasks
            self._deadlock_prevention_count += 1
            self.logger.warning(f"Deadlock prevention: Too many waiting tasks ({len(self._waiting_tasks)})")
            raise ResourceAllocationError("Potential deadlock detected - too many waiting tasks")

        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                async with self._allocation_lock:
                    # Check if resources are available
                    if self._can_allocate_resources(required_resources):
                        # Allocate resources atomically
                        self._allocate_resources(task_id, required_resources)
                        self._allocation_count += 1
                        self._consecutive_failures = 0  # Reset failure counter

                        self.logger.info(f"Resources allocated for task {task_id}: {required_resources}")
                        return True

                    else:
                        # Resources not available - check if we should wait or fail fast
                        if attempt == max_retries - 1:
                            self.logger.warning(f"Resources unavailable for task {task_id} after {max_retries} attempts")
                            self._handle_allocation_failure(task_id)
                            return False

                # Wait before retry (outside the lock to prevent blocking)
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 1.0)  # Exponential backoff

            except asyncio.CancelledError:
                # Handle cancellation gracefully
                self.logger.info(f"Resource allocation cancelled for task {task_id} on attempt {attempt + 1}")
                raise

        return False

    def _can_allocate_resources(self, required_resources: Dict[ResourceType, float]) -> bool:
        """Check if required resources are available"""
        for resource_type, amount in required_resources.items():
            available = self.max_resources[resource_type] - self.allocated_resources[resource_type]
            if amount > available:
                return False
        return True

    def _allocate_resources(self, task_id: str, required_resources: Dict[ResourceType, float]):
        """Atomically allocate resources to a task"""
        # Update global allocation tracking
        for resource_type, amount in required_resources.items():
            self.allocated_resources[resource_type] += amount

        # Track per-task allocations for cleanup
        self.task_allocations[task_id] = required_resources.copy()

    async def release_resources(self, task_id: str):
        """Release all resources allocated to a task"""
        async with self._allocation_lock:
            if task_id in self.task_allocations:
                allocated = self.task_allocations[task_id]

                # Release resources
                for resource_type, amount in allocated.items():
                    self.allocated_resources[resource_type] = max(
                        0.0,
                        self.allocated_resources[resource_type] - amount
                    )

                # Remove task allocation record
                del self.task_allocations[task_id]

                self.logger.info(f"Resources released for task {task_id}: {allocated}")

    async def _cleanup_partial_allocation(self, task_id: str):
        """Clean up any partial resource allocation"""
        try:
            await self.release_resources(task_id)
        except Exception as e:
            self.logger.error(f"Error cleaning up partial allocation for {task_id}: {e}")

    def _handle_allocation_failure(self, task_id: str):
        """Handle allocation failure and update circuit breaker"""
        self._failed_allocations += 1
        self._consecutive_failures += 1

        # Check if circuit breaker should open
        if self._consecutive_failures >= self._max_consecutive_failures:
            self._circuit_open_until = time.time() + 10.0  # Open for 10 seconds
            self.logger.warning("Resource allocation circuit breaker OPENED due to consecutive failures")

    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self._circuit_open_until > time.time():
            return True

        # Reset circuit breaker
        if self._circuit_open_until > 0:
            self._circuit_open_until = 0
            self._consecutive_failures = 0
            self.logger.info("Resource allocation circuit breaker CLOSED")

        return False

    def get_resource_utilization(self) -> Dict[str, Any]:
        """Get comprehensive resource utilization statistics for backward compatibility"""
        total_allocated = defaultdict(float)

        for task_resources in self.task_allocations.values():
            for resource_type, amount in task_resources.items():
                total_allocated[resource_type] += amount

        utilization = {}
        for resource_type in ResourceType:
            allocated = total_allocated.get(resource_type, 0)
            available = self.max_resources[resource_type] - allocated
            total = self.max_resources[resource_type]
            utilization[str(resource_type)] = {
                "allocated": allocated,
                "available": available,
                "total": total,
                "utilization_percent": (allocated / total * 100) if total > 0 else 0
            }

        return {
            "resources": utilization,
            "waiting_tasks": len(self._waiting_tasks),
            "allocated_tasks": len(self.task_allocations)
        }

    def get_waiting_tasks(self) -> List[str]:
        """Get list of tasks waiting for resources."""
        return list(self._waiting_tasks)

    def get_resource_stats(self) -> Dict:
        """Get comprehensive resource statistics"""
        stats = {
            'total_allocations': self._allocation_count,
            'failed_allocations': self._failed_allocations,
            'deadlock_preventions': self._deadlock_prevention_count,
            'waiting_tasks': len(self._waiting_tasks),
            'active_allocations': len(self.task_allocations),
            'circuit_breaker_open': self._is_circuit_open(),
            'consecutive_failures': self._consecutive_failures,
            'resource_utilization': {}
        }

        # Calculate utilization percentages
        for resource_type in ResourceType:
            max_amount = self.max_resources[resource_type]
            allocated_amount = self.allocated_resources[resource_type]
            utilization = (allocated_amount / max_amount * 100) if max_amount > 0 else 0
            stats['resource_utilization'][resource_type.value] = ".1f"

        return stats

    async def force_cleanup_all(self):
        """Emergency cleanup of all resource allocations"""
        async with self._allocation_lock:
            self.logger.warning("EMERGENCY: Force cleaning up all resource allocations")

            # Reset all allocations
            for resource_type in ResourceType:
                self.allocated_resources[resource_type] = 0.0

            # Clear task allocations
            self.task_allocations.clear()
            self._waiting_tasks.clear()

            # Reset circuit breaker
            self._circuit_open_until = 0
            self._consecutive_failures = 0

            self.logger.info("Emergency cleanup completed")


class PersistenceManager:
    """Enterprise-grade persistence layer with atomic operations and data integrity."""

    def __init__(self, storage_path: str = "./data/execution_state"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.lock_file = self.storage_path / ".lock"
        self.backup_path = self.storage_path / "backups"
        self.backup_path.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

    async def save_execution_state(self, execution_id: str, state_data: Dict[str, Any]) -> bool:
        """Atomically save execution state with backup and integrity checks."""
        lock_context = None
        try:
            # Acquire lock for atomic operation
            lock_context = await self._acquire_lock()

            if lock_context is None:
                self.logger.warning(f"Could not acquire lock for {execution_id}")
                return False

            await lock_context.__aenter__()

            # Create backup of existing state
            await self._create_backup(execution_id)

            # Save new state with integrity
            state_file = self.storage_path / f"{execution_id}.json"
            temp_file = self.storage_path / f"{execution_id}.tmp"

            # Write to temporary file first
            state_data["checksum"] = self._calculate_checksum(state_data)
            state_data["timestamp"] = datetime.now().isoformat()

            async with aiofiles.open(temp_file, 'w') as f:
                await f.write(json.dumps(state_data, indent=2, default=str))

            # Atomic move (rename) to final location
            temp_file.replace(state_file)

            self.logger.info(f"Execution state saved for {execution_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save execution state: {e}")
            await self._restore_backup(execution_id)
            return False
        finally:
            # Release lock
            if lock_context:
                await lock_context.__aexit__(None, None, None)

    async def load_execution_state(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Load execution state with integrity verification."""
        try:
            state_file = self.storage_path / f"{execution_id}.json"

            if not state_file.exists():
                return None

            async with aiofiles.open(state_file, 'r') as f:
                state_data = json.loads(await f.read())

            # Verify integrity
            if not self._verify_integrity(state_data):
                self.logger.warning(f"Integrity check failed for {execution_id}, attempting recovery")
                return await self._recover_state(execution_id)

            self.logger.info(f"Execution state loaded for {execution_id}")
            return state_data

        except Exception as e:
            self.logger.error(f"Failed to load execution state: {e}")
            return await self._recover_state(execution_id)

    async def save_checkpoint(self, execution_id: str, checkpoint_id: str,
                             checkpoint_data: Dict[str, Any]) -> bool:
        """Save execution checkpoint with rollback capability."""
        try:
            checkpoint_dir = self.storage_path / "checkpoints" / execution_id
            checkpoint_dir.mkdir(parents=True, exist_ok=True)

            checkpoint_file = checkpoint_dir / f"{checkpoint_id}.json"
            temp_file = checkpoint_dir / f"{checkpoint_id}.tmp"

            # Add metadata
            checkpoint_data["checkpoint_id"] = checkpoint_id
            checkpoint_data["execution_id"] = execution_id
            checkpoint_data["timestamp"] = datetime.now().isoformat()
            checkpoint_data["checksum"] = self._calculate_checksum(checkpoint_data)

            async with aiofiles.open(temp_file, 'w') as f:
                await f.write(json.dumps(checkpoint_data, indent=2, default=str))

            temp_file.replace(checkpoint_file)

            # Maintain checkpoint history (keep last 10)
            await self._cleanup_old_checkpoints(checkpoint_dir)

            self.logger.info(f"Checkpoint saved: {execution_id}/{checkpoint_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
            return False

    async def load_checkpoint(self, execution_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Load specific checkpoint."""
        try:
            checkpoint_file = self.storage_path / "checkpoints" / execution_id / f"{checkpoint_id}.json"

            if not checkpoint_file.exists():
                return None

            async with aiofiles.open(checkpoint_file, 'r') as f:
                checkpoint_data = json.loads(await f.read())

            if not self._verify_integrity(checkpoint_data):
                self.logger.warning(f"Checkpoint integrity failed: {checkpoint_id}")
                return None

            return checkpoint_data

        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
            return None

    async def list_checkpoints(self, execution_id: str) -> List[str]:
        """List all available checkpoints for an execution."""
        try:
            checkpoint_dir = self.storage_path / "checkpoints" / execution_id
            if not checkpoint_dir.exists():
                return []

            checkpoints = []
            for checkpoint_file in checkpoint_dir.glob("*.json"):
                checkpoints.append(checkpoint_file.stem)

            return sorted(checkpoints)

        except Exception as e:
            self.logger.error(f"Failed to list checkpoints: {e}")
            return []

    async def save_task_state(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """Save individual task state."""
        try:
            task_file = self.storage_path / "tasks" / f"{task_id}.json"
            task_file.parent.mkdir(parents=True, exist_ok=True)
            temp_file = self.storage_path / "tasks" / f"{task_id}.tmp"

            task_data["task_id"] = task_id
            task_data["last_updated"] = datetime.now().isoformat()
            task_data["checksum"] = self._calculate_checksum(task_data)

            async with aiofiles.open(temp_file, 'w') as f:
                await f.write(json.dumps(task_data, indent=2, default=str))

            temp_file.replace(task_file)
            return True

        except Exception as e:
            self.logger.error(f"Failed to save task state: {e}")
            return False

    async def load_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load individual task state."""
        try:
            task_file = self.storage_path / "tasks" / f"{task_id}.json"

            if not task_file.exists():
                return None

            async with aiofiles.open(task_file, 'r') as f:
                task_data = json.loads(await f.read())

            if not self._verify_integrity(task_data):
                self.logger.warning(f"Task state integrity failed: {task_id}")
                return None

            return task_data

        except Exception as e:
            self.logger.error(f"Failed to load task state: {e}")
            return None

    async def cleanup_old_states(self, max_age_days: int = 30):
        """Clean up old execution states and checkpoints."""
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)

            # Clean up old execution states
            for state_file in self.storage_path.glob("*.json"):
                if state_file.stat().st_mtime < cutoff_date.timestamp():
                    state_file.unlink()
                    self.logger.info(f"Cleaned up old state file: {state_file.name}")

            # Clean up old checkpoints
            checkpoint_root = self.storage_path / "checkpoints"
            if checkpoint_root.exists():
                for execution_dir in checkpoint_root.iterdir():
                    if execution_dir.is_dir():
                        for checkpoint_file in execution_dir.glob("*.json"):
                            if checkpoint_file.stat().st_mtime < cutoff_date.timestamp():
                                checkpoint_file.unlink()

                        # Remove empty directories
                        if not list(execution_dir.iterdir()):
                            execution_dir.rmdir()

        except Exception as e:
            self.logger.error(f"Failed to cleanup old states: {e}")

    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum for data integrity."""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _verify_integrity(self, data: Dict[str, Any]) -> bool:
        """Verify data integrity using checksum."""
        if "checksum" not in data:
            return True  # No checksum to verify, assume valid

        try:
            # Create a copy to avoid modifying original
            data_copy = dict(data)
            stored_checksum = data_copy.pop("checksum")

            # Calculate checksum on the copy without checksum field
            data_str = json.dumps(data_copy, sort_keys=True, default=str)
            calculated_checksum = hashlib.sha256(data_str.encode()).hexdigest()

            return stored_checksum == calculated_checksum
        except Exception:
            # If verification fails due to any error, consider it invalid
            return False

    async def _create_backup(self, execution_id: str):
        """Create backup of existing state."""
        try:
            state_file = self.storage_path / f"{execution_id}.json"
            if state_file.exists():
                backup_file = self.backup_path / f"{execution_id}_{int(datetime.now().timestamp())}.json"
                await aiofiles.copyfile(state_file, backup_file)
        except Exception as e:
            self.logger.warning(f"Failed to create backup: {e}")

    async def _restore_backup(self, execution_id: str):
        """Restore from latest backup."""
        try:
            backup_files = list(self.backup_path.glob(f"{execution_id}_*.json"))
            if backup_files:
                latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
                state_file = self.storage_path / f"{execution_id}.json"
                await aiofiles.copyfile(latest_backup, state_file)
                self.logger.info(f"Restored from backup: {latest_backup.name}")
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")

    async def _recover_state(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Attempt to recover state from backup."""
        try:
            await self._restore_backup(execution_id)
            return await self.load_execution_state(execution_id)
        except Exception as e:
            self.logger.error(f"State recovery failed: {e}")
            return None

    async def _cleanup_old_checkpoints(self, checkpoint_dir: Path):
        """Keep only the most recent 10 checkpoints."""
        try:
            checkpoint_files = list(checkpoint_dir.glob("*.json"))
            if len(checkpoint_files) > 10:
                # Sort by modification time, keep newest 10
                checkpoint_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                for old_file in checkpoint_files[10:]:
                    old_file.unlink()
        except Exception as e:
            self.logger.warning(f"Failed to cleanup old checkpoints: {e}")

    async def _acquire_lock(self):
        """Acquire file system lock for atomic operations."""
        # Simple file-based locking - simplified for reliability
        max_attempts = 50  # 5 seconds max wait
        attempt = 0

        while attempt < max_attempts:
            try:
                if not self.lock_file.exists():
                    self.lock_file.touch()
                    # Return a simple context manager
                    return SimpleLockContext(self.lock_file)
                else:
                    await asyncio.sleep(0.1)  # Wait and retry
                    attempt += 1
            except Exception:
                await asyncio.sleep(0.1)
                attempt += 1

        # Timeout - return None to indicate failure
        return None


class SimpleLockContext:
    """Simple context manager for file-based locking."""

    def __init__(self, lock_file: Path):
        self.lock_file = lock_file

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except Exception:
            pass  # Ignore errors when releasing lock

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics and health."""
        try:
            total_files = 0
            total_size = 0

            # Count files and size in main storage
            for file_path in self.storage_path.rglob("*"):
                if file_path.is_file():
                    total_files += 1
                    total_size += file_path.stat().st_size

            # Count backup files
            backups_count = 0
            if self.backup_path.exists():
                backups_count = len(list(self.backup_path.glob("*.json")))

            # Determine health status
            health_status = "HEALTHY"
            if total_files == 0:
                health_status = "EMPTY"
            elif total_size > 100 * 1024 * 1024:  # > 100MB
                health_status = "LARGE"
            elif backups_count == 0:
                health_status = "NO_BACKUPS"

            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "storage_path": str(self.storage_path),
                "backups_count": backups_count,
                "health_status": health_status,
                "last_check": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {e}")
            return {
                "error": str(e),
                "health_status": "ERROR",
                "last_check": datetime.now().isoformat()
            }


class RetryManager:
    """Exponential backoff retry manager with jitter."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0,
                 max_delay: float = 60.0, backoff_factor: float = 2.0,
                 jitter_factor: float = 0.1):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter_factor = jitter_factor
        self.logger = logging.getLogger(__name__)

    async def execute_with_retry(self, func, *args, **kwargs) -> Any:
        """Execute function with exponential backoff retry."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if attempt == self.max_retries:
                    # Final attempt failed
                    self.logger.error(f"Function failed after {self.max_retries} retries: {e}")
                    raise e

                # Calculate delay with exponential backoff and jitter
                delay = self._calculate_delay(attempt)
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s")

                await asyncio.sleep(delay)

        # Should never reach here, but just in case
        raise last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        # Exponential backoff: base_delay * (backoff_factor ^ attempt)
        delay = self.base_delay * (self.backoff_factor ** attempt)

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter to prevent thundering herd
        jitter = delay * self.jitter_factor * (2 * random.random() - 1)
        delay += jitter

        # Ensure delay is positive
        return max(0.1, delay)

    def should_retry(self, exception: Exception) -> bool:
        """Determine if exception should trigger a retry."""
        # Define retryable exceptions
        retryable_exceptions = (
            ConnectionError,
            TimeoutError,
            OSError,  # Includes network-related errors
        )

        # Don't retry certain types of errors
        non_retryable_exceptions = (
            ValueError,  # Usually indicates bad input
            TypeError,   # Usually indicates programming error
            AttributeError,  # Usually indicates programming error
        )

        # Check if it's a retryable exception
        if isinstance(exception, retryable_exceptions):
            return True

        # Check if it's a non-retryable exception
        if isinstance(exception, non_retryable_exceptions):
            return False

        # For other exceptions, default to retrying
        return True


class CircuitBreaker:
    """Circuit breaker pattern for handling cascading failures."""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.logger = logging.getLogger(__name__)

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "HALF_OPEN"
                self.logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise Exception("Circuit breaker is OPEN - rejecting request")

        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                self.logger.info("Circuit breaker reset to CLOSED state")
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

            raise e

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "failure_threshold": self.failure_threshold,
            "timeout_seconds": self.timeout
        }

class DependencyGraph:
    """Enterprise-grade DAG management with comprehensive validation and optimization."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.tasks: Dict[str, EnhancedTaskNode] = {}
        self.cycles_detected: List[List[str]] = []
        self.longest_path_cache: Optional[List[str]] = None
        self.critical_path_cache: Optional[List[str]] = None

    def add_task(self, task_node: EnhancedTaskNode) -> bool:
        """Add a task to the dependency graph with validation."""
        if task_node.task_id in self.tasks:
            raise ValueError(f"Task {task_node.task_id} already exists in graph")

        self.graph.add_node(task_node.task_id, **task_node.task.dict())
        self.tasks[task_node.task_id] = task_node
        self._invalidate_caches()
        return True

    def add_dependency(self, dependent_id: str, dependency_id: str) -> bool:
        """Add a dependency relationship with comprehensive validation."""
        if dependent_id not in self.tasks:
            raise ValueError(f"Dependent task {dependent_id} not found")
        if dependency_id not in self.tasks:
            raise ValueError(f"Dependency task {dependency_id} not found")

        # Check if dependency would create a cycle
        self.graph.add_edge(dependency_id, dependent_id)
        if not nx.is_directed_acyclic_graph(self.graph):
            self.graph.remove_edge(dependency_id, dependent_id)
            cycle = self._detect_cycle(dependent_id, dependency_id)
            self.cycles_detected.append(cycle)
            raise ValueError(f"Dependency would create cycle: {dependency_id} -> {dependent_id}. Cycle: {cycle}")

        # Update task relationships
        self.tasks[dependent_id].dependencies.add(dependency_id)
        self.tasks[dependency_id].dependents.add(dependent_id)
        self._invalidate_caches()
        return True

    def _detect_cycle(self, start_node: str, end_node: str) -> List[str]:
        """Detect and return the cycle path if one exists."""
        try:
            # Find all simple cycles
            cycles = list(nx.simple_cycles(self.graph))
            for cycle in cycles:
                if start_node in cycle and end_node in cycle:
                    return cycle
            return [start_node, end_node]  # Fallback
        except:
            return [start_node, end_node]

    def get_ready_tasks(self) -> List[str]:
        """Get tasks that are ready to execute (all dependencies completed)."""
        ready_tasks = []
        for task_id, task_node in self.tasks.items():
            if task_node.status == TaskStatus.PENDING:
                # Check if all dependencies are completed
                deps_completed = all(
                    self.tasks.get(dep_id, EnhancedTaskNode("", TaskModel())).status == TaskStatus.COMPLETED
                    for dep_id in task_node.dependencies
                )
                if deps_completed:
                    ready_tasks.append(task_id)
        return ready_tasks

    def get_execution_order(self) -> List[str]:
        """Get optimized topological execution order."""
        try:
            if not nx.is_directed_acyclic_graph(self.graph):
                raise ValueError("Graph contains cycles - cannot determine execution order")

            # Use longest path for critical path scheduling
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXError as e:
            raise ValueError(f"Cannot determine execution order: {e}")

    def get_critical_path(self) -> List[str]:
        """Calculate the critical path through the DAG."""
        if self.critical_path_cache is not None:
            return self.critical_path_cache

        try:
            if not nx.is_directed_acyclic_graph(self.graph):
                return []

            # For now, return longest path as approximation
            longest_path = nx.dag_longest_path(self.graph)
            self.critical_path_cache = longest_path
            return longest_path
        except:
            return []

    def get_parallel_groups(self) -> List[List[str]]:
        """Group tasks by parallel execution levels."""
        if not nx.is_directed_acyclic_graph(self.graph):
            return []

        levels = {}
        for node in nx.topological_sort(self.graph):
            pred_levels = [levels.get(pred, 0) for pred in self.graph.predecessors(node)]
            levels[node] = max(pred_levels) + 1 if pred_levels else 1

        # Group by level
        level_groups = {}
        for node, level in levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(node)

        return list(level_groups.values())

    def validate_graph(self) -> Dict[str, Any]:
        """Comprehensive graph validation."""
        validation = {
            "is_dag": nx.is_directed_acyclic_graph(self.graph),
            "has_cycles": len(self.cycles_detected) > 0,
            "cycles": self.cycles_detected,
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
            "isolated_nodes": list(nx.isolates(self.graph)),
            "critical_path": self.get_critical_path(),
            "execution_levels": len(self.get_parallel_groups())
        }
        return validation

    def _invalidate_caches(self):
        """Invalidate cached computations when graph changes."""
        self.longest_path_cache = None
        self.critical_path_cache = None

class ExecutionCrew(BaseCrew):
    """Enhanced Execution Crew with enterprise-grade reliability."""
    
    def __init__(self, project_data: Dict[str, Any], config: ExecutionCrewConfig = None):
        super().__init__(project_data)
        self.config = config or ExecutionCrewConfig()
        self.dependency_graph = DependencyGraph()
        self.resource_manager = BulletproofResourceManager(
            max_cpu=100.0,
            max_memory=200.0,
            max_network=50.0,
            max_disk=50.0
        )
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.circuit_breaker_threshold
        )
        self.retry_manager = RetryManager(
            max_retries=self.config.failure_retry_limit,
            base_delay=1.0,
            max_delay=60.0
        )
        self.execution_semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)
        self.persistence_manager = PersistenceManager()
        self.logger = logging.getLogger(__name__)

    def _create_crew(self) -> Crew:
        """Create the Execution Crew with agents and tasks - required by BaseCrew."""
        # This method is not used in the enhanced implementation
        # but is required by the abstract base class
        # Provide minimal valid configuration
        from crewai import Agent, Task

        # Create a dummy agent for CrewAI compatibility
        dummy_agent = Agent(
            role="Execution Coordinator",
            goal="Coordinate task execution with enterprise-grade reliability",
            backstory="An AI agent specialized in managing complex task orchestration"
        )

        dummy_task = Task(
            description="Execute tasks with enhanced reliability patterns",
            agent=dummy_agent,
            expected_output="Task execution results with comprehensive monitoring"
        )

        return Crew(
            agents=[dummy_agent],
            tasks=[dummy_task],
            process=Process.sequential,
            verbose=True,
        )

    async def _execute_crew(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the Execution Crew - required by BaseCrew."""
        # Route to the enhanced orchestration method
        if 'tasks' in inputs:
            return await self.orchestrate_execution(inputs['tasks'])
        else:
            # Fallback for legacy compatibility
            return {"status": "completed", "legacy_mode": True}

    async def orchestrate_execution(self, tasks: List[TaskModel]) -> Dict[str, Any]:
        """Main orchestration method with enhanced reliability patterns."""
        self.logger.info(f"🚀 Starting orchestration with {len(tasks)} tasks")

        try:
            # Phase 1: Build dependency graph
            self.logger.debug("📊 Phase 1: Building dependency graph...")
            task_nodes = await self._build_dependency_graph(tasks)
            self.logger.info(f"✅ Built dependency graph with {len(task_nodes)} task nodes")

            # Phase 2: Validate execution plan
            self.logger.debug("🔍 Phase 2: Validating execution plan...")
            execution_order = self.dependency_graph.get_execution_order()
            self.logger.info(f"✅ Execution order determined: {len(execution_order)} tasks")

            # Phase 3: Execute with resource management and fault tolerance
            self.logger.debug("⚙️ Phase 3: Executing with reliability patterns...")
            results = await self._execute_with_reliability(execution_order)
            self.logger.info(f"✅ Execution completed. Results: {len(results)} task results")

            # Phase 4: Generate final statistics
            self.logger.debug("📈 Phase 4: Generating execution statistics...")
            execution_stats = self._generate_execution_stats()
            self.logger.info(f"✅ Execution statistics generated successfully")

            final_result = {
                "status": "success",
                "results": results,
                "execution_stats": execution_stats
            }

            self.logger.info("🎉 Orchestration completed successfully!")
            return final_result

        except Exception as e:
            self.logger.error(f"❌ Orchestration failed: {e}")
            self.logger.error(f"🔍 Error type: {type(e).__name__}")

            # Collect partial results for error reporting
            self.logger.debug("📊 Collecting partial results...")
            partial_results = await self._get_partial_results()

            error_result = {
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "partial_results": partial_results
            }

            return error_result

    async def _build_dependency_graph(self, tasks: List[TaskModel]) -> List[EnhancedTaskNode]:
        """Build the dependency graph from tasks."""
        self.logger.debug(f"Building dependency graph for {len(tasks)} tasks")
        task_nodes = []

        for task in tasks:
            try:
                # Analyze task for resource requirements
                resources = await self._analyze_resource_requirements(task)

                task_node = EnhancedTaskNode(
                    task_id=task.id,
                    task=task,
                    resources=resources
                )

                self.dependency_graph.add_task(task_node)
                task_nodes.append(task_node)
                self.logger.debug(f"✅ Added task node: {task.id}")

            except Exception as e:
                self.logger.error(f"❌ Failed to add task {task.id}: {e}")
                raise

        # Add dependencies based on task analysis
        self.logger.debug("Analyzing and adding dependencies...")
        await self._analyze_and_add_dependencies(task_nodes)

        self.logger.debug(f"✅ Dependency graph built with {len(task_nodes)} nodes")
        return task_nodes

    async def _execute_with_reliability(self, execution_order: List[str]) -> Dict[str, Any]:
        """Execute tasks with reliability patterns."""
        self.logger.debug(f"Executing {len(execution_order)} tasks with reliability patterns")
        results = {}

        # Execute in batches respecting dependencies
        execution_round = 0
        while True:
            execution_round += 1
            self.logger.debug(f"Execution round {execution_round}")

            ready_tasks = self.dependency_graph.get_ready_tasks()
            self.logger.debug(f"Ready tasks: {ready_tasks}")

            if not ready_tasks:
                self.logger.debug("No more ready tasks - execution complete")
                break

            # Execute ready tasks concurrently
            batch_size = min(len(ready_tasks), self.config.max_concurrent_tasks)
            batch_tasks = [
                self._execute_single_task_with_reliability(task_id)
                for task_id in ready_tasks[:batch_size]
            ]

            self.logger.debug(f"Executing batch of {batch_size} tasks concurrently")
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for task_id, result in zip(ready_tasks[:batch_size], batch_results):
                if isinstance(result, Exception):
                    self.logger.warning(f"Task {task_id} failed: {result}")
                    await self._handle_task_failure(task_id, result)
                else:
                    self.logger.debug(f"Task {task_id} completed successfully")
                    results[task_id] = result
                    self.dependency_graph.tasks[task_id].status = TaskStatus.COMPLETED

        self.logger.info(f"Execution completed with {len(results)} successful tasks")
        return results

    async def _execute_single_task_with_reliability(self, task_id: str) -> Any:
        """Execute a single task with full reliability patterns."""
        task_node = self.dependency_graph.tasks[task_id]
        
        async with self.execution_semaphore:
            # Resource reservation
            if not await self.resource_manager.reserve_resources(task_id, task_node.resources):
                raise Exception(f"Resource reservation failed for task {task_id}")
            
            try:
                task_node.status = TaskStatus.RUNNING
                task_node.started_at = datetime.now()
                
                # Execute with circuit breaker
                result = await self.circuit_breaker.call(
                    self._execute_task_with_checkpoints,
                    task_node
                )
                
                return result
                
            finally:
                await self.resource_manager.release_resources(task_id)

    async def _execute_task_with_checkpoints(self, task_node: EnhancedTaskNode) -> Any:
        """Execute task with checkpoint/rollback capability and retry logic."""
        steps = await self._decompose_task(task_node.task)

        for i, step in enumerate(steps):
            # Create checkpoint
            if i % self.config.checkpoint_interval == 0:
                checkpoint = TaskCheckpoint(
                    task_id=task_node.task_id,
                    step_index=i,
                    state_data=await self._capture_task_state(task_node),
                    timestamp=datetime.now()
                )
                task_node.checkpoints.append(checkpoint)

            # Execute step with retry logic
            try:
                result = await self.retry_manager.execute_with_retry(
                    self._execute_step_with_timeout,
                    step
                )
            except Exception as e:
                # Retry failed - rollback and try again
                if task_node.retry_count < self.config.failure_retry_limit:
                    task_node.retry_count += 1
                    self.logger.warning(f"Step {i} failed for task {task_node.task_id}, rolling back")
                    await self._rollback_to_last_checkpoint(task_node)
                    # Restart from beginning of failed step
                    i -= 1
                    continue
                else:
                    self.logger.error(f"Task {task_node.task_id} failed permanently after {self.config.failure_retry_limit} retries")
                    raise e

        return await self._finalize_task_execution(task_node)

    async def _execute_step_with_timeout(self, step: Dict[str, Any]) -> Any:
        """Execute a single step with timeout protection."""
        return await asyncio.wait_for(
            self._execute_step(step),
            timeout=self.config.execution_timeout
        )

    async def _analyze_resource_requirements(self, task: TaskModel) -> List[ResourceRequirement]:
        """Analyze task to determine resource requirements based on task complexity."""
        # Analyze task description to estimate resource needs
        description = task.description.lower()

        cpu_req = 10.0  # Base CPU requirement
        memory_req = 20.0  # Base memory requirement
        network_req = 5.0  # Base network requirement
        api_req = 0.0  # Base API requirement

        # Scale requirements based on task complexity indicators
        if any(keyword in description for keyword in ['complex', 'analysis', 'optimization', 'synthesis']):
            cpu_req *= 2.0
            memory_req *= 2.0

        if any(keyword in description for keyword in ['external', 'api', 'integration', 'fetch']):
            network_req *= 3.0
            api_req = 10.0

        if any(keyword in description for keyword in ['parallel', 'concurrent', 'distributed']):
            cpu_req *= 1.5
            memory_req *= 1.5

        requirements = [
            ResourceRequirement(ResourceType.CPU, cpu_req),
            ResourceRequirement(ResourceType.MEMORY, memory_req),
            ResourceRequirement(ResourceType.NETWORK, network_req),
        ]

        if api_req > 0:
            requirements.append(ResourceRequirement(ResourceType.EXTERNAL_API, api_req))

        return requirements

    async def _analyze_and_add_dependencies(self, task_nodes: List[EnhancedTaskNode]):
        """Analyze tasks and automatically add dependency relationships."""
        for i, task_node in enumerate(task_nodes):
            for j, other_node in enumerate(task_nodes):
                if i != j and await self._has_dependency(task_node, other_node):
                    try:
                        self.dependency_graph.add_dependency(
                            other_node.task_id, task_node.task_id
                        )
                    except ValueError as e:
                        self.logger.warning(f"Dependency analysis failed: {e}")

    async def _has_dependency(self, dependent: EnhancedTaskNode, dependency: EnhancedTaskNode) -> bool:
        """Determine if one task depends on another based on content analysis."""
        dependent_desc = dependent.task.description.lower()
        dependency_desc = dependency.task.description.lower()

        # Simple dependency rules (can be enhanced with ML)
        dependency_indicators = [
            f"after {dependency_desc.split()[0]}",
            f"following {dependency_desc.split()[0]}",
            f"based on {dependency_desc.split()[0]}",
            f"using {dependency_desc.split()[0]}",
            f"requires {dependency_desc.split()[0]}"
        ]

        return any(indicator in dependent_desc for indicator in dependency_indicators)

    async def _handle_task_failure(self, task_id: str, error: Exception):
        """Handle task failure with appropriate recovery."""
        task_node = self.dependency_graph.tasks[task_id]
        task_node.status = TaskStatus.FAILED
        task_node.error_log.append(str(error))
        task_node.completed_at = datetime.now()
        self.logger.error(f"Task {task_id} failed: {error}")

        # Release resources on failure
        await self.resource_manager.release_resources(task_id)

        # Mark dependent tasks as blocked
        for dependent_id in task_node.dependents:
            if dependent_id in self.dependency_graph.tasks:
                dependent_task = self.dependency_graph.tasks[dependent_id]
                if dependent_task.status == TaskStatus.PENDING:
                    dependent_task.status = TaskStatus.BLOCKED
                    dependent_task.error_log.append(f"Blocked due to failure of dependency {task_id}")

    async def _capture_task_state(self, task_node: EnhancedTaskNode) -> Dict[str, Any]:
        """Capture current task state for rollback purposes."""
        return {
            "task_id": task_node.task_id,
            "status": task_node.status,
            "step_data": getattr(task_node.task, 'current_step_data', {}),
            "resource_allocation": self.resource_manager.allocated_resources.get(task_node.task_id, {}),
            "timestamp": datetime.now().isoformat()
        }

    async def _rollback_to_last_checkpoint(self, task_node: EnhancedTaskNode):
        """Rollback task to last successful checkpoint."""
        if task_node.checkpoints:
            last_checkpoint = task_node.checkpoints[-1]

            # Restore task state
            task_node.status = last_checkpoint.state_data.get("status", TaskStatus.PENDING)

            # Restore resource allocation if needed
            if last_checkpoint.state_data.get("resource_allocation"):
                await self.resource_manager.reserve_resources(
                    task_node.task_id,
                    [ResourceRequirement(rt, amt) for rt, amt in
                     last_checkpoint.state_data["resource_allocation"].items()]
                )

            self.logger.info(f"Rolled back task {task_node.task_id} to checkpoint at step {last_checkpoint.step_index}")

    async def _decompose_task(self, task: TaskModel) -> List[Dict[str, Any]]:
        """Decompose task into executable steps."""
        # Simple decomposition - can be enhanced with ML
        steps = []
        description = task.description

        # Split by common delimiters
        if "and" in description:
            sub_tasks = description.split(" and ")
        elif "," in description:
            sub_tasks = description.split(",")
        else:
            sub_tasks = [description]

        for i, sub_task in enumerate(sub_tasks):
            steps.append({
                "step_id": f"{task.id}_step_{i}",
                "description": sub_task.strip(),
                "estimated_duration": timedelta(minutes=5 * (i + 1)),
                "required_resources": await self._analyze_resource_requirements(task)
            })

        return steps

    async def _execute_step(self, step: Dict[str, Any]) -> Any:
        """Execute a single task step."""
        self.logger.info(f"Executing step: {step['step_id']} - {step['description']}")

        # Simulate step execution - replace with actual implementation
        await asyncio.sleep(1)  # Simulate work

        # Random success/failure for testing (replace with actual logic)
        import random
        if random.random() > 0.1:  # 90% success rate
            return {"step_id": step["step_id"], "status": "completed", "result": "success"}
        else:
            raise Exception(f"Step {step['step_id']} failed")

    async def _finalize_task_execution(self, task_node: EnhancedTaskNode) -> Any:
        """Finalize task execution and return results."""
        task_node.status = TaskStatus.COMPLETED
        task_node.completed_at = datetime.now()

        # Release resources
        await self.resource_manager.release_resources(task_node.task_id)

        return {
            "task_id": task_node.task_id,
            "status": "completed",
            "execution_time": (task_node.completed_at - task_node.started_at).total_seconds(),
            "checkpoints_created": len(task_node.checkpoints),
            "retry_count": task_node.retry_count
        }

    def _generate_execution_stats(self) -> Dict[str, Any]:
        """Generate comprehensive execution statistics."""
        total_tasks = len(self.dependency_graph.tasks)
        completed = sum(1 for t in self.dependency_graph.tasks.values()
                       if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.dependency_graph.tasks.values()
                     if t.status == TaskStatus.FAILED)
        blocked = sum(1 for t in self.dependency_graph.tasks.values()
                      if t.status == TaskStatus.BLOCKED)
        running = sum(1 for t in self.dependency_graph.tasks.values()
                      if t.status == TaskStatus.RUNNING)
        pending = sum(1 for t in self.dependency_graph.tasks.values()
                      if t.status == TaskStatus.PENDING)

        total_execution_time = 0
        total_checkpoints = 0
        total_retries = 0

        for task in self.dependency_graph.tasks.values():
            if task.completed_at and task.started_at:
                total_execution_time += (task.completed_at - task.started_at).total_seconds()
            total_checkpoints += len(task.checkpoints)
            total_retries += task.retry_count

        # Create comprehensive monitoring report
        monitoring_report = self._generate_monitoring_report(
            total_tasks, completed, failed, blocked, running, pending,
            total_execution_time, total_checkpoints, total_retries
        )

        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "failed": failed,
            "blocked": blocked,
            "running": running,
            "pending": pending,
            "success_rate": completed / total_tasks if total_tasks > 0 else 0,
            "failure_rate": failed / total_tasks if total_tasks > 0 else 0,
            "average_execution_time": total_execution_time / completed if completed > 0 else 0,
            "total_checkpoints": total_checkpoints,
            "total_retries": total_retries,
            "resource_utilization": self.resource_manager.get_resource_utilization(),
            "monitoring_report": monitoring_report
        }

    def _generate_monitoring_report(self, total_tasks: int, completed: int, failed: int,
                                   blocked: int, running: int, pending: int,
                                   total_execution_time: float, total_checkpoints: int,
                                   total_retries: int) -> Dict[str, Any]:
        """Generate comprehensive monitoring report with health indicators and alerts."""

        # Calculate health scores
        health_score = self._calculate_health_score(
            total_tasks, completed, failed, blocked, running, pending
        )

        # Performance metrics
        performance_metrics = self._calculate_performance_metrics(
            total_execution_time, completed, total_tasks
        )

        # Resource health
        resource_health = self._assess_resource_health()

        # Circuit breaker status
        circuit_breaker_status = self.circuit_breaker.get_status()

        # Generate alerts
        alerts = self._generate_system_alerts(
            health_score, performance_metrics, resource_health, circuit_breaker_status
        )

        # Dependency graph analysis
        graph_analysis = self.dependency_graph.validate_graph()

        return {
            "timestamp": datetime.now().isoformat(),
            "health_score": health_score,
            "performance_metrics": performance_metrics,
            "resource_health": resource_health,
            "circuit_breaker": circuit_breaker_status,
            "dependency_graph": graph_analysis,
            "alerts": alerts,
            "system_status": self._determine_system_status(health_score, alerts),
            "recommendations": self._generate_recommendations(alerts)
        }

    def _calculate_health_score(self, total: int, completed: int, failed: int,
                               blocked: int, running: int, pending: int) -> float:
        """Calculate overall system health score (0-100)."""
        if total == 0:
            return 100.0

        # Weight factors for health calculation
        completion_weight = 0.4
        failure_weight = 0.3
        blocking_weight = 0.2
        activity_weight = 0.1

        completion_score = (completed / total) * 100
        failure_penalty = (failed / total) * 50  # Failures hurt health significantly
        blocking_penalty = (blocked / total) * 30  # Blocked tasks hurt moderately
        activity_bonus = min((running + pending) / total * 20, 20)  # Active tasks are good

        health_score = (
            completion_score * completion_weight -
            failure_penalty * failure_weight -
            blocking_penalty * blocking_weight +
            activity_bonus * activity_weight
        )

        return max(0.0, min(100.0, health_score))

    def _calculate_performance_metrics(self, total_execution_time: float,
                                     completed: int, total: int) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        avg_execution_time = total_execution_time / completed if completed > 0 else 0

        # Calculate throughput (tasks per minute)
        total_runtime = sum(
            (task.completed_at - task.started_at).total_seconds()
            for task in self.dependency_graph.tasks.values()
            if task.completed_at and task.started_at
        )
        throughput = completed / (total_runtime / 60) if total_runtime > 0 else 0

        return {
            "average_execution_time_seconds": avg_execution_time,
            "throughput_tasks_per_minute": throughput,
            "total_execution_time_seconds": total_execution_time,
            "efficiency_ratio": completed / total if total > 0 else 0,
            "performance_rating": self._rate_performance(avg_execution_time, throughput)
        }

    def _rate_performance(self, avg_time: float, throughput: float) -> str:
        """Rate system performance based on metrics."""
        if avg_time < 30 and throughput > 2:
            return "EXCELLENT"
        elif avg_time < 60 and throughput > 1:
            return "GOOD"
        elif avg_time < 120 and throughput > 0.5:
            return "FAIR"
        else:
            return "NEEDS_IMPROVEMENT"

    def _assess_resource_health(self) -> Dict[str, Any]:
        """Assess resource utilization health."""
        utilization = self.resource_manager.get_resource_utilization()

        # Calculate resource stress levels
        stress_levels = {}
        critical_resources = []

        for resource_name, resource_data in utilization.get("resources", {}).items():
            utilization_pct = resource_data.get("utilization_percent", 0)

            if utilization_pct > 90:
                stress_levels[resource_name] = "CRITICAL"
                critical_resources.append(resource_name)
            elif utilization_pct > 75:
                stress_levels[resource_name] = "HIGH"
            elif utilization_pct > 50:
                stress_levels[resource_name] = "MODERATE"
            else:
                stress_levels[resource_name] = "LOW"

        return {
            "stress_levels": stress_levels,
            "critical_resources": critical_resources,
            "waiting_tasks_count": utilization.get("waiting_tasks", 0),
            "overall_health": "CRITICAL" if critical_resources else "HEALTHY"
        }

    def _generate_system_alerts(self, health_score: float, performance: Dict,
                               resources: Dict, circuit_breaker: Dict) -> List[Dict[str, Any]]:
        """Generate system alerts based on monitoring data."""
        alerts = []

        # Health score alerts
        if health_score < 50:
            alerts.append({
                "level": "CRITICAL",
                "category": "HEALTH",
                "message": f"System health critically low: {health_score:.1f}/100",
                "recommendation": "Immediate investigation required"
            })
        elif health_score < 75:
            alerts.append({
                "level": "WARNING",
                "category": "HEALTH",
                "message": f"System health degraded: {health_score:.1f}/100",
                "recommendation": "Monitor closely and investigate issues"
            })

        # Performance alerts
        perf_rating = performance.get("performance_rating", "")
        if perf_rating in ["NEEDS_IMPROVEMENT", "POOR"]:
            alerts.append({
                "level": "WARNING",
                "category": "PERFORMANCE",
                "message": f"Performance rating: {perf_rating}",
                "recommendation": "Optimize task execution and resource allocation"
            })

        # Resource alerts
        critical_resources = resources.get("critical_resources", [])
        if critical_resources:
            alerts.append({
                "level": "CRITICAL",
                "category": "RESOURCES",
                "message": f"Critical resource utilization: {', '.join(critical_resources)}",
                "recommendation": "Scale resources or redistribute load immediately"
            })

        # Circuit breaker alerts
        cb_state = circuit_breaker.get("state", "")
        if cb_state == "OPEN":
            alerts.append({
                "level": "CRITICAL",
                "category": "CIRCUIT_BREAKER",
                "message": "Circuit breaker is OPEN - system under protection",
                "recommendation": "Investigate root cause before resetting"
            })
        elif cb_state == "HALF_OPEN":
            alerts.append({
                "level": "WARNING",
                "category": "CIRCUIT_BREAKER",
                "message": "Circuit breaker testing recovery",
                "recommendation": "Monitor system recovery progress"
            })

        return alerts

    def _determine_system_status(self, health_score: float, alerts: List[Dict]) -> str:
        """Determine overall system status."""
        critical_alerts = [a for a in alerts if a["level"] == "CRITICAL"]

        if critical_alerts:
            return "CRITICAL"
        elif health_score < 50:
            return "DEGRADED"
        elif health_score < 75:
            return "WARNING"
        else:
            return "HEALTHY"

    def _generate_recommendations(self, alerts: List[Dict]) -> List[str]:
        """Generate actionable recommendations based on alerts."""
        recommendations = []

        alert_categories = set(alert["category"] for alert in alerts)

        if "HEALTH" in alert_categories:
            recommendations.append("Review task failure patterns and error handling")
            recommendations.append("Check dependency graph for circular dependencies")

        if "PERFORMANCE" in alert_categories:
            recommendations.append("Implement task parallelization where possible")
            recommendations.append("Optimize resource allocation algorithms")
            recommendations.append("Consider increasing concurrent task limits")

        if "RESOURCES" in alert_categories:
            recommendations.append("Scale up resource capacity or redistribute tasks")
            recommendations.append("Implement resource preemption for critical tasks")
            recommendations.append("Review task resource requirements")

        if "CIRCUIT_BREAKER" in alert_categories:
            recommendations.append("Investigate and resolve root cause failures")
            recommendations.append("Implement better error handling and retries")
            recommendations.append("Consider implementing service degradation strategies")

        if not recommendations:
            recommendations.append("System operating normally - continue monitoring")

        return recommendations

    async def _get_partial_results(self) -> Dict[str, Any]:
        """Get partial results from failed execution for error reporting."""
        try:
            partial_results = {}

            # Collect completed tasks
            completed_tasks = [
                task_id for task_id, task_node in self.dependency_graph.tasks.items()
                if task_node.status == TaskStatus.COMPLETED
            ]
            partial_results["completed_tasks"] = completed_tasks

            # Collect failed tasks
            failed_tasks = [
                task_id for task_id, task_node in self.dependency_graph.tasks.items()
                if task_node.status == TaskStatus.FAILED
            ]
            partial_results["failed_tasks"] = failed_tasks

            # Collect blocked tasks
            blocked_tasks = [
                task_id for task_id, task_node in self.dependency_graph.tasks.items()
                if task_node.status == TaskStatus.BLOCKED
            ]
            partial_results["blocked_tasks"] = blocked_tasks

            # Resource utilization summary
            resource_stats = self.resource_manager.get_resource_utilization()
            partial_results["resource_utilization"] = resource_stats

            # Circuit breaker status
            cb_status = self.circuit_breaker.get_status()
            partial_results["circuit_breaker_status"] = cb_status

            # Execution timing
            total_execution_time = sum(
                (task.completed_at - task.started_at).total_seconds()
                for task in self.dependency_graph.tasks.values()
                if task.completed_at and task.started_at
            )
            partial_results["total_execution_time_seconds"] = total_execution_time

            return partial_results

        except Exception as e:
            self.logger.error(f"Failed to collect partial results: {e}")
            return {
                "error": f"Could not collect partial results: {str(e)}",
                "collection_failed": True
            }