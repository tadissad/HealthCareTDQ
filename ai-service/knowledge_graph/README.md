# Knowledge Graph

This folder seeds and queries the Neo4j knowledge graph used by the AI service.

## What it shows
- User nodes
- Product nodes
- Category nodes
- Action events
- Session grouping
- Purchase and review links
- Co-purchase relationships
- Exported JSON and Markdown reports

## Files
- `seed_neo4j.py`: imports `data_user500.csv` into Neo4j
- `query_neo4j.py`: runs evidence queries and exports results
- `run_knowledge_graph.py`: one-command pipeline for seed and query export

## Run

### One command

```bash
python run_knowledge_graph.py --data ../data_user500.csv --output ../knowledge_graph_output
```

### Separate commands

```bash
python seed_neo4j.py --data ../data_user500.csv
python query_neo4j.py --output ../knowledge_graph_output
```

## Neo4j requirements
- URI: `bolt://localhost:7687`
- Username: `neo4j`
- Password: `health123`

## Output files
- `knowledge_graph_output/overview.json`
- `knowledge_graph_output/top_categories.json`
- `knowledge_graph_output/top_products.json`
- `knowledge_graph_output/user_journey.json`
- `knowledge_graph_output/co_purchase.json`
- `knowledge_graph_output/graph_report.md`
- `knowledge_graph_output/graph_summary.json`
- `knowledge_graph_output/seed_summary.json`

## What to screenshot
1. Terminal showing seeding success
2. Neo4j Browser graph with User-Product-Category relationships
3. Query result tables from the Markdown report
4. `graph_report.md` or the JSON outputs
