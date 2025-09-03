"""
Mermaid tools for tractionbuild agents.
"""

from typing import Dict, List, Any, Optional
from crewai.tools import BaseTool
import json


class MermaidTools:
    """Mermaid diagram generation tools for agents."""
    
    def __init__(self):
        """Initialize Mermaid tools."""
        pass
    
    def generate_flowchart(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
        """
        Generate Mermaid flowchart.
        
        Args:
            nodes: List of nodes
            edges: List of edges
            
        Returns:
            Mermaid flowchart code
        """
        # Placeholder implementation
        flowchart = "graph TD\n"
        
        for node in nodes:
            node_id = node.get("id", "node")
            node_label = node.get("label", node_id)
            flowchart += f"    {node_id}[{node_label}]\n"
        
        for edge in edges:
            from_node = edge.get("from", "start")
            to_node = edge.get("to", "end")
            label = edge.get("label", "")
            if label:
                flowchart += f"    {from_node} -->|{label}| {to_node}\n"
            else:
                flowchart += f"    {from_node} --> {to_node}\n"
        
        return flowchart
    
    def generate_sequence_diagram(self, participants: List[str], interactions: List[Dict[str, Any]]) -> str:
        """
        Generate Mermaid sequence diagram.
        
        Args:
            participants: List of participants
            interactions: List of interactions
            
        Returns:
            Mermaid sequence diagram code
        """
        # Placeholder implementation
        diagram = "sequenceDiagram\n"
        
        for participant in participants:
            diagram += f"    participant {participant}\n"
        
        for interaction in interactions:
            from_participant = interaction.get("from", "A")
            to_participant = interaction.get("to", "B")
            message = interaction.get("message", "Message")
            diagram += f"    {from_participant}->>{to_participant}: {message}\n"
        
        return diagram


# CrewAI Tool wrappers
def create_flowchart_tool() -> BaseTool:
    """Create a flowchart generation tool for CrewAI."""
    return BaseTool(
        name="generate_flowchart",
        description="Generate Mermaid flowchart",
        func=MermaidTools().generate_flowchart
    )


def create_sequence_diagram_tool() -> BaseTool:
    """Create a sequence diagram generation tool for CrewAI."""
    return BaseTool(
        name="generate_sequence_diagram",
        description="Generate Mermaid sequence diagram",
        func=MermaidTools().generate_sequence_diagram
    ) 