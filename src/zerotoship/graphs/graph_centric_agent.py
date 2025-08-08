"""
Graph-Centric Agent for ZeroToShip.
Handles graph-based execution, task orchestration, and dependency management.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

from crewai import Agent
from pydantic import BaseModel, Field


@dataclass
class GraphNode:
    """Represents a node in the execution graph."""
    id: str
    task_type: str
    description: str
    dependencies: List[str]
    estimated_duration: int  # minutes
    priority: str  # high, medium, low
    status: str  # pending, running, completed, failed
    metadata: Dict[str, Any]


class GraphAgentConfig(BaseModel):
    """Configuration for the Graph Agent."""
    
    max_concurrent_nodes: int = Field(default=10, description="Maximum concurrent nodes")
    enable_parallel_execution: bool = Field(default=True, description="Enable parallel execution")
    enable_dependency_resolution: bool = Field(default=True, description="Enable dependency resolution")
    enable_cycle_detection: bool = Field(default=True, description="Enable cycle detection")
    enable_optimization: bool = Field(default=True, description="Enable graph optimization")
    timeout_seconds: int = Field(default=300, description="Execution timeout in seconds")


class GraphAgent:
    """Graph-Centric Agent for managing execution graphs and task orchestration."""
    
    def __init__(self, config: Optional[GraphAgentConfig] = None):
        """Initialize the Graph Agent."""
        self.config = config or GraphAgentConfig()
        self.logger = logging.getLogger(__name__)
        self.execution_graph: Dict[str, GraphNode] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
    def build_graph(self, task_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build execution graph from task graph.
        
        Args:
            task_graph: Task graph with nodes and dependencies
            
        Returns:
            Execution graph with optimized structure
        """
        self.logger.info(f"Building execution graph from {len(task_graph.get('nodes', []))} tasks")
        
        # Convert task graph to execution graph
        execution_graph = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "total_nodes": len(task_graph.get('nodes', [])),
                "optimization_level": "standard"
            }
        }
        
        # Process nodes
        for node_data in task_graph.get('nodes', []):
            node = GraphNode(
                id=node_data.get('id', f"node_{len(execution_graph['nodes'])}"),
                task_type=node_data.get('type', 'task'),
                description=node_data.get('description', ''),
                dependencies=node_data.get('dependencies', []),
                estimated_duration=node_data.get('estimated_duration', 60),
                priority=node_data.get('priority', 'medium'),
                status='pending',
                metadata=node_data.get('metadata', {})
            )
            
            execution_graph['nodes'].append({
                'id': node.id,
                'task_type': node.task_type,
                'description': node.description,
                'dependencies': node.dependencies,
                'estimated_duration': node.estimated_duration,
                'priority': node.priority,
                'status': node.status,
                'metadata': node.metadata
            })
            
            # Add edges for dependencies
            for dep in node.dependencies:
                execution_graph['edges'].append({
                    'from': dep,
                    'to': node.id,
                    'type': 'dependency'
                })
        
        # Optimize graph if enabled
        if self.config.enable_optimization:
            execution_graph = self._optimize_graph(execution_graph)
        
        # Detect cycles if enabled
        if self.config.enable_cycle_detection:
            cycles = self._detect_cycles(execution_graph)
            if cycles:
                self.logger.warning(f"Detected {len(cycles)} cycles in execution graph")
                execution_graph['metadata']['cycles_detected'] = cycles
        
        self.execution_graph = {node['id']: GraphNode(**node) for node in execution_graph['nodes']}
        
        self.logger.info(f"Built execution graph with {len(execution_graph['nodes'])} nodes and {len(execution_graph['edges'])} edges")
        return execution_graph
    
    def _optimize_graph(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize execution graph for better performance."""
        # Sort nodes by priority and dependencies
        nodes = graph['nodes']
        nodes.sort(key=lambda x: (
            {'high': 0, 'medium': 1, 'low': 2}.get(x['priority'], 1),
            len(x['dependencies'])
        ))
        
        # Update graph with optimized node order
        graph['nodes'] = nodes
        graph['metadata']['optimization_level'] = 'optimized'
        
        return graph
    
    def _detect_cycles(self, graph: Dict[str, Any]) -> List[List[str]]:
        """Detect cycles in the execution graph."""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str, path: List[str]):
            if node_id in rec_stack:
                cycle_start = path.index(node_id)
                cycles.append(path[cycle_start:] + [node_id])
                return
            
            if node_id in visited:
                return
            
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            # Find outgoing edges
            for edge in graph['edges']:
                if edge['from'] == node_id:
                    dfs(edge['to'], path.copy())
            
            rec_stack.remove(node_id)
            path.pop()
        
        # Check each node for cycles
        for node in graph['nodes']:
            if node['id'] not in visited:
                dfs(node['id'], [])
        
        return cycles
    
    async def execute_graph(self, graph: Dict[str, Any], crew_controller: Any) -> Dict[str, Any]:
        """
        Execute the graph using the crew controller.
        
        Args:
            graph: Execution graph to execute
            crew_controller: Crew controller for task execution
            
        Returns:
            Execution results
        """
        self.logger.info(f"Executing graph with {len(graph['nodes'])} nodes")
        
        results = {
            "completed_nodes": [],
            "failed_nodes": [],
            "execution_time": 0,
            "parallel_execution": self.config.enable_parallel_execution
        }
        
        start_time = datetime.now()
        
        try:
            if self.config.enable_parallel_execution:
                results = await self._execute_parallel(graph, crew_controller)
            else:
                results = await self._execute_sequential(graph, crew_controller)
                
        except Exception as e:
            self.logger.error(f"Graph execution failed: {e}")
            results["error"] = str(e)
        
        results["execution_time"] = (datetime.now() - start_time).total_seconds()
        
        # Store execution history
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "graph_id": graph.get('metadata', {}).get('id', 'unknown'),
            "results": results
        })
        
        return results
    
    async def _execute_parallel(self, graph: Dict[str, Any], crew_controller: Any) -> Dict[str, Any]:
        """Execute graph nodes in parallel where possible."""
        results = {
            "completed_nodes": [],
            "failed_nodes": [],
            "parallel_execution": True
        }
        
        # Group nodes by execution level (dependency depth)
        execution_levels = self._group_by_execution_level(graph)
        
        for level, nodes in execution_levels.items():
            self.logger.info(f"Executing level {level} with {len(nodes)} nodes")
            
            # Execute nodes in current level concurrently
            tasks = []
            for node in nodes:
                task = self._execute_node(node, crew_controller)
                tasks.append(task)
            
            # Wait for all tasks in current level to complete
            level_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(level_results):
                if isinstance(result, Exception):
                    results["failed_nodes"].append({
                        "node_id": nodes[i]['id'],
                        "error": str(result)
                    })
                else:
                    results["completed_nodes"].append({
                        "node_id": nodes[i]['id'],
                        "result": result
                    })
        
        return results
    
    async def _execute_sequential(self, graph: Dict[str, Any], crew_controller: Any) -> Dict[str, Any]:
        """Execute graph nodes sequentially."""
        results = {
            "completed_nodes": [],
            "failed_nodes": [],
            "parallel_execution": False
        }
        
        # Sort nodes by dependencies
        sorted_nodes = self._topological_sort(graph)
        
        for node in sorted_nodes:
            try:
                result = await self._execute_node(node, crew_controller)
                results["completed_nodes"].append({
                    "node_id": node['id'],
                    "result": result
                })
            except Exception as e:
                self.logger.error(f"Node {node['id']} execution failed: {e}")
                results["failed_nodes"].append({
                    "node_id": node['id'],
                    "error": str(e)
                })
        
        return results
    
    async def _execute_node(self, node: Dict[str, Any], crew_controller: Any) -> Dict[str, Any]:
        """Execute a single node."""
        self.logger.info(f"Executing node: {node['id']} - {node['description']}")
        
        # Map node type to crew method
        crew_mapping = {
            'validation': crew_controller._run_validator_crew,
            'execution': crew_controller._run_execution_crew,
            'build': crew_controller._run_builder_crew,
            'marketing': crew_controller._run_marketing_crew,
            'feedback': crew_controller._run_feedback_crew
        }
        
        crew_method = crew_mapping.get(node['task_type'], crew_controller._run_validator_crew)
        
        # Execute with timeout
        try:
            async with asyncio.timeout(self.config.timeout_seconds):
                result = await crew_method(node['description'])
                return result
        except asyncio.TimeoutError:
            raise Exception(f"Node execution timed out after {self.config.timeout_seconds} seconds")
    
    def _group_by_execution_level(self, graph: Dict[str, Any]) -> Dict[int, List[Dict[str, Any]]]:
        """Group nodes by execution level based on dependencies."""
        levels = {}
        node_depths = {}
        
        # Calculate depth for each node
        for node in graph['nodes']:
            depth = self._calculate_node_depth(node, graph)
            node_depths[node['id']] = depth
            
            if depth not in levels:
                levels[depth] = []
            levels[depth].append(node)
        
        return levels
    
    def _calculate_node_depth(self, node: Dict[str, Any], graph: Dict[str, Any]) -> int:
        """Calculate the depth of a node based on its dependencies."""
        if not node['dependencies']:
            return 0
        
        max_depth = 0
        for dep_id in node['dependencies']:
            # Find dependency node
            dep_node = next((n for n in graph['nodes'] if n['id'] == dep_id), None)
            if dep_node:
                dep_depth = self._calculate_node_depth(dep_node, graph)
                max_depth = max(max_depth, dep_depth + 1)
        
        return max_depth
    
    def _topological_sort(self, graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Sort nodes topologically for sequential execution."""
        # Create adjacency list
        adj_list = {node['id']: [] for node in graph['nodes']}
        in_degree = {node['id']: 0 for node in graph['nodes']}
        
        for edge in graph['edges']:
            adj_list[edge['from']].append(edge['to'])
            in_degree[edge['to']] += 1
        
        # Kahn's algorithm for topological sort
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        sorted_nodes = []
        
        while queue:
            node_id = queue.pop(0)
            sorted_nodes.append(next(n for n in graph['nodes'] if n['id'] == node_id))
            
            for neighbor in adj_list[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return sorted_nodes
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {
            "total_executions": len(self.execution_history),
            "average_execution_time": sum(
                h['results'].get('execution_time', 0) for h in self.execution_history
            ) / max(len(self.execution_history), 1),
            "success_rate": len([
                h for h in self.execution_history 
                if not h['results'].get('failed_nodes')
            ]) / max(len(self.execution_history), 1),
            "last_execution": self.execution_history[-1] if self.execution_history else None
        } 