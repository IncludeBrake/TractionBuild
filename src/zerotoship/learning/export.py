import json
from ..database.neo4j_writer import neo4j_writer

def export_training_example(project_id: str, output_path: str):
    if not neo4j_writer._driver: return

    query = """
        MATCH (p:Project {id: $pid})
        OPTIONAL MATCH (p)-[:PRODUCES]->(v:Artifact {kind: 'validation'})
        OPTIONAL MATCH (p)-[:PRODUCES]->(a:Artifact {kind: 'advisory'})
        RETURN {
            project_id: p.id,
            idea: p.idea,
            validation_output: v.output,
            advisory_mission: a.output
        } AS training_example
    """
    with neo4j_writer._driver.session() as session:
        result = session.run(query, pid=project_id)
        record = result.single()
        if record and record['training_example']:
            with open(output_path, 'a') as f: # Append to JSONL file
                f.write(json.dumps(record['training_example']) + '\n')
            print(f"Appended training example for {project_id} to {output_path}")