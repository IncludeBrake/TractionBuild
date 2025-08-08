"""
Mermaid Exporter for ZeroToShip.
Handles visualization generation for execution graphs and project workflows.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from pydantic import BaseModel, Field


class MermaidExporterConfig(BaseModel):
    """Configuration for the Mermaid Exporter."""
    
    enable_syntax_highlighting: bool = Field(default=True, description="Enable syntax highlighting")
    enable_theme_customization: bool = Field(default=True, description="Enable theme customization")
    enable_interactive_features: bool = Field(default=True, description="Enable interactive features")
    max_nodes_per_diagram: int = Field(default=50, description="Maximum nodes per diagram")
    diagram_theme: str = Field(default="default", description="Diagram theme")
    enable_animations: bool = Field(default=False, description="Enable animations")


class MermaidExporter:
    """Mermaid Exporter for generating visualizations of execution graphs."""
    
    def __init__(self, config: Optional[MermaidExporterConfig] = None):
        """Initialize the Mermaid Exporter."""
        self.config = config or MermaidExporterConfig()
        self.logger = logging.getLogger(__name__)
        
    def export(self, execution_graph: Dict[str, Any], diagram_type: str = "flowchart") -> str:
        """
        Export execution graph to Mermaid diagram.
        
        Args:
            execution_graph: Execution graph to visualize
            diagram_type: Type of diagram (flowchart, gantt, sequence)
            
        Returns:
            Mermaid diagram code
        """
        self.logger.info(f"Exporting execution graph to {diagram_type} diagram")
        
        if diagram_type == "flowchart":
            return self._export_flowchart(execution_graph)
        elif diagram_type == "gantt":
            return self._export_gantt(execution_graph)
        elif diagram_type == "sequence":
            return self._export_sequence(execution_graph)
        else:
            self.logger.warning(f"Unknown diagram type: {diagram_type}, using flowchart")
            return self._export_flowchart(execution_graph)
    
    def _export_flowchart(self, execution_graph: Dict[str, Any]) -> str:
        """Export execution graph as flowchart."""
        nodes = execution_graph.get('nodes', [])
        edges = execution_graph.get('edges', [])
        
        # Limit nodes if configured
        if len(nodes) > self.config.max_nodes_per_diagram:
            self.logger.warning(f"Graph has {len(nodes)} nodes, limiting to {self.config.max_nodes_per_diagram}")
            nodes = nodes[:self.config.max_nodes_per_diagram]
        
        # Generate Mermaid flowchart
        mermaid_code = ["flowchart TD"]
        
        # Add nodes
        for node in nodes:
            node_id = self._sanitize_id(node['id'])
            node_label = self._sanitize_label(node.get('name', node['id']))
            node_type = node.get('type', 'task')
            
            # Add styling based on node type
            style = self._get_node_style(node_type, node.get('status', 'pending'))
            mermaid_code.append(f"    {node_id}[{node_label}] {style}")
        
        # Add edges
        for edge in edges:
            from_id = self._sanitize_id(edge['from'])
            to_id = self._sanitize_id(edge['to'])
            edge_type = edge.get('type', 'dependency')
            
            # Add edge styling
            edge_style = self._get_edge_style(edge_type)
            mermaid_code.append(f"    {from_id} {edge_style} {to_id}")
        
        # Add theme if enabled
        if self.config.enable_theme_customization:
            mermaid_code.append(f"    %% theme: {self.config.diagram_theme}")
        
        return "\n".join(mermaid_code)
    
    def _export_gantt(self, execution_graph: Dict[str, Any]) -> str:
        """Export execution graph as Gantt chart."""
        nodes = execution_graph.get('nodes', [])
        
        # Limit nodes if configured
        if len(nodes) > self.config.max_nodes_per_diagram:
            nodes = nodes[:self.config.max_nodes_per_diagram]
        
        # Generate Mermaid Gantt chart
        mermaid_code = ["gantt"]
        mermaid_code.append("    title Project Execution Timeline")
        mermaid_code.append("    dateFormat  YYYY-MM-DD")
        mermaid_code.append("    section Validation")
        
        # Group nodes by type
        validation_nodes = [n for n in nodes if n.get('type') == 'validation']
        execution_nodes = [n for n in nodes if n.get('type') == 'execution']
        build_nodes = [n for n in nodes if n.get('type') == 'build']
        marketing_nodes = [n for n in nodes if n.get('type') == 'marketing']
        feedback_nodes = [n for n in nodes if n.get('type') == 'feedback']
        
        # Add validation tasks
        for node in validation_nodes:
            task_name = self._sanitize_label(node.get('name', node['id']))
            duration = node.get('estimated_duration', 60)
            mermaid_code.append(f"    {task_name} :{duration}m")
        
        mermaid_code.append("    section Execution")
        for node in execution_nodes:
            task_name = self._sanitize_label(node.get('name', node['id']))
            duration = node.get('estimated_duration', 60)
            mermaid_code.append(f"    {task_name} :{duration}m")
        
        mermaid_code.append("    section Build")
        for node in build_nodes:
            task_name = self._sanitize_label(node.get('name', node['id']))
            duration = node.get('estimated_duration', 60)
            mermaid_code.append(f"    {task_name} :{duration}m")
        
        mermaid_code.append("    section Marketing")
        for node in marketing_nodes:
            task_name = self._sanitize_label(node.get('name', node['id']))
            duration = node.get('estimated_duration', 60)
            mermaid_code.append(f"    {task_name} :{duration}m")
        
        mermaid_code.append("    section Feedback")
        for node in feedback_nodes:
            task_name = self._sanitize_label(node.get('name', node['id']))
            duration = node.get('estimated_duration', 60)
            mermaid_code.append(f"    {task_name} :{duration}m")
        
        return "\n".join(mermaid_code)
    
    def _export_sequence(self, execution_graph: Dict[str, Any]) -> str:
        """Export execution graph as sequence diagram."""
        nodes = execution_graph.get('nodes', [])
        
        # Limit nodes if configured
        if len(nodes) > self.config.max_nodes_per_diagram:
            nodes = nodes[:self.config.max_nodes_per_diagram]
        
        # Generate Mermaid sequence diagram
        mermaid_code = ["sequenceDiagram"]
        mermaid_code.append("    participant V as Validator")
        mermaid_code.append("    participant E as Execution")
        mermaid_code.append("    participant B as Builder")
        mermaid_code.append("    participant M as Marketing")
        mermaid_code.append("    participant F as Feedback")
        
        # Add sequence based on task types
        for node in nodes:
            node_type = node.get('type', 'task')
            task_name = self._sanitize_label(node.get('name', node['id']))
            
            if node_type == 'validation':
                mermaid_code.append(f"    V->>E: {task_name}")
            elif node_type == 'execution':
                mermaid_code.append(f"    E->>B: {task_name}")
            elif node_type == 'build':
                mermaid_code.append(f"    B->>F: {task_name}")
            elif node_type == 'marketing':
                mermaid_code.append(f"    M->>F: {task_name}")
            elif node_type == 'feedback':
                mermaid_code.append(f"    F->>V: {task_name}")
        
        return "\n".join(mermaid_code)
    
    def _sanitize_id(self, node_id: str) -> str:
        """Sanitize node ID for Mermaid compatibility."""
        # Replace special characters with underscores
        sanitized = node_id.replace('-', '_').replace(' ', '_').replace('.', '_')
        # Ensure it starts with a letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = f"node_{sanitized}"
        return sanitized
    
    def _sanitize_label(self, label: str) -> str:
        """Sanitize node label for Mermaid compatibility."""
        # Truncate long labels
        if len(label) > 30:
            label = label[:27] + "..."
        # Replace special characters
        label = label.replace('"', "'").replace('\n', ' ')
        return label
    
    def _get_node_style(self, node_type: str, status: str) -> str:
        """Get node styling based on type and status."""
        base_style = ""
        
        # Type-based styling
        if node_type == 'validation':
            base_style = ":::validation"
        elif node_type == 'execution':
            base_style = ":::execution"
        elif node_type == 'build':
            base_style = ":::build"
        elif node_type == 'marketing':
            base_style = ":::marketing"
        elif node_type == 'feedback':
            base_style = ":::feedback"
        
        # Status-based styling
        if status == 'completed':
            base_style += " :::completed"
        elif status == 'failed':
            base_style += " :::failed"
        elif status == 'running':
            base_style += " :::running"
        
        return base_style
    
    def _get_edge_style(self, edge_type: str) -> str:
        """Get edge styling based on type."""
        if edge_type == 'dependency':
            return "-->"
        elif edge_type == 'data_flow':
            return "-.->"
        elif edge_type == 'control_flow':
            return "==>"
        else:
            return "-->"
    
    def export_to_html(self, execution_graph: Dict[str, Any], diagram_type: str = "flowchart") -> str:
        """
        Export execution graph to HTML with embedded Mermaid.
        
        Args:
            execution_graph: Execution graph to visualize
            diagram_type: Type of diagram
            
        Returns:
            HTML with embedded Mermaid diagram
        """
        mermaid_code = self.export(execution_graph, diagram_type)
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ZeroToShip Execution Graph</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .mermaid {{
            text-align: center;
            margin: 20px 0;
        }}
        .metadata {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .metadata h3 {{
            margin-top: 0;
            color: #333;
        }}
        .metadata p {{
            margin: 5px 0;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>ZeroToShip Execution Graph</h1>
        
        <div class="metadata">
            <h3>Graph Information</h3>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Total Nodes:</strong> {len(execution_graph.get('nodes', []))}</p>
            <p><strong>Total Edges:</strong> {len(execution_graph.get('edges', []))}</p>
            <p><strong>Diagram Type:</strong> {diagram_type.title()}</p>
        </div>
        
        <div class="mermaid">
{mermaid_code}
        </div>
    </div>
    
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: '{self.config.diagram_theme}',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true
            }}
        }});
    </script>
</body>
</html>
        """
        
        return html_template
    
    def export_to_svg(self, execution_graph: Dict[str, Any], diagram_type: str = "flowchart") -> str:
        """
        Export execution graph to SVG format.
        
        Args:
            execution_graph: Execution graph to visualize
            diagram_type: Type of diagram
            
        Returns:
            SVG content
        """
        # This would require a Mermaid CLI or server-side rendering
        # For now, return a placeholder SVG
        mermaid_code = self.export(execution_graph, diagram_type)
        
        # Placeholder SVG - in production, this would be generated by Mermaid
        svg_template = f"""
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
    <rect width="800" height="600" fill="#ffffff"/>
    <text x="400" y="50" text-anchor="middle" font-family="Arial" font-size="24" fill="#333">
        ZeroToShip Execution Graph
    </text>
    <text x="400" y="80" text-anchor="middle" font-family="Arial" font-size="14" fill="#666">
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </text>
    <text x="400" y="100" text-anchor="middle" font-family="Arial" font-size="12" fill="#666">
        Nodes: {len(execution_graph.get('nodes', []))} | Edges: {len(execution_graph.get('edges', []))}
    </text>
    <text x="400" y="300" text-anchor="middle" font-family="Arial" font-size="16" fill="#999">
        Mermaid Diagram (SVG export not implemented)
    </text>
    <text x="400" y="320" text-anchor="middle" font-family="Arial" font-size="12" fill="#999">
        Use HTML export for full visualization
    </text>
</svg>
        """
        
        return svg_template
    
    def get_export_stats(self) -> Dict[str, Any]:
        """Get export statistics."""
        return {
            "supported_diagram_types": ["flowchart", "gantt", "sequence"],
            "max_nodes_per_diagram": self.config.max_nodes_per_diagram,
            "theme": self.config.diagram_theme,
            "features_enabled": {
                "syntax_highlighting": self.config.enable_syntax_highlighting,
                "theme_customization": self.config.enable_theme_customization,
                "interactive_features": self.config.enable_interactive_features,
                "animations": self.config.enable_animations
            }
        } 