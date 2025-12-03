import json
import os
from typing import Dict, Any
from ..core.context_bus import ContextBus

async def export_context_to_graph(context_bus: ContextBus, output_dir: str = "output"):
    history = await context_bus.get_history()
    
    nodes = set()
    edges = []
    
    executed_states = []
    for event in history:
        event_name = event.get("name", "")
        if event_name.endswith("_executed"):
            state = event_name.replace("_executed", "")
            nodes.add(state)
            executed_states.append(state)

    for i in range(len(executed_states) - 1):
        edges.append({
            "source": executed_states[i],
            "target": executed_states[i+1]
        })

    # Add final state if workflow completed
    snapshot = await context_bus.snapshot()
    final_workflow_metrics = snapshot.get("workflow_metrics", {})
    final_state = final_workflow_metrics.get("final_state")
    if final_state:
        nodes.add(final_state)
        if executed_states and executed_states[-1] != final_state:
             edges.append({
                "source": executed_states[-1],
                "target": final_state
            })


    graph_data = {
        "nodes": [{"id": node} for node in list(nodes)],
        "edges": edges,
        "full_history": history, # include for debugging
    }

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, "context_graph.json")
    with open(output_path, 'w') as f:
        json.dump(graph_data, f, indent=2)

    print(f"Context graph exported to {output_path}")
