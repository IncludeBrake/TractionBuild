"""
Mermaid utilities for tractionbuild.
"""

from typing import Dict, List, Any, Optional


def generate_mermaid_diagram(
    diagram_type: str,
    data: Dict[str, Any],
    title: Optional[str] = None
) -> str:
    """
    Generate Mermaid diagram.
    
    Args:
        diagram_type: Type of diagram (flowchart, sequence, etc.)
        data: Diagram data
        title: Diagram title
        
    Returns:
        Mermaid diagram code
    """
    if diagram_type == "flowchart":
        return _generate_flowchart(data, title)
    elif diagram_type == "sequence":
        return _generate_sequence_diagram(data, title)
    elif diagram_type == "gantt":
        return _generate_gantt_chart(data, title)
    else:
        raise ValueError(f"Unsupported diagram type: {diagram_type}")


def _generate_flowchart(data: Dict[str, Any], title: Optional[str] = None) -> str:
    """Generate flowchart diagram."""
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    
    diagram = "graph TD\n"
    
    if title:
        diagram += f"    title[{title}]\n"
    
    for node in nodes:
        node_id = node.get("id", "node")
        node_label = node.get("label", node_id)
        node_type = node.get("type", "default")
        
        if node_type == "start":
            diagram += f"    {node_id}([{node_label}])\n"
        elif node_type == "end":
            diagram += f"    {node_id}([{node_label}])\n"
        elif node_type == "decision":
            diagram += f"    {node_id}{{{node_label}}}\n"
        else:
            diagram += f"    {node_id}[{node_label}]\n"
    
    for edge in edges:
        from_node = edge.get("from", "start")
        to_node = edge.get("to", "end")
        label = edge.get("label", "")
        
        if label:
            diagram += f"    {from_node} -->|{label}| {to_node}\n"
        else:
            diagram += f"    {from_node} --> {to_node}\n"
    
    return diagram


def _generate_sequence_diagram(data: Dict[str, Any], title: Optional[str] = None) -> str:
    """Generate sequence diagram."""
    participants = data.get("participants", [])
    interactions = data.get("interactions", [])
    
    diagram = "sequenceDiagram\n"
    
    if title:
        diagram += f"    title {title}\n"
    
    for participant in participants:
        diagram += f"    participant {participant}\n"
    
    for interaction in interactions:
        from_participant = interaction.get("from", "A")
        to_participant = interaction.get("to", "B")
        message = interaction.get("message", "Message")
        interaction_type = interaction.get("type", "->>")
        
        diagram += f"    {from_participant}{interaction_type}{to_participant}: {message}\n"
    
    return diagram


def _generate_gantt_chart(data: Dict[str, Any], title: Optional[str] = None) -> str:
    """Generate Gantt chart."""
    tasks = data.get("tasks", [])
    
    diagram = "gantt\n"
    
    if title:
        diagram += f"    title {title}\n"
    
    diagram += "    dateFormat  YYYY-MM-DD\n"
    diagram += "    section Tasks\n"
    
    for task in tasks:
        task_name = task.get("name", "Task")
        start_date = task.get("start", "2024-01-01")
        end_date = task.get("end", "2024-01-31")
        
        diagram += f"    {task_name} :{start_date}, {end_date}\n"
    
    return diagram 