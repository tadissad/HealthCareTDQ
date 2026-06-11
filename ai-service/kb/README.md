# Unified KB (ai-service)

This folder is the single source of AI knowledge data.

## Sources
- `sources/prompt1.seed.json`: seed product catalog
- `sources/prompt2.seed.json`: symptom/disease taxonomy and product mappings
- `sources/prompt3.seed.json`: long-form QA chunks
- `sources/benhdaday.seed.csv`: clinical disease table
- `sources/faq.seed.txt`: FAQ corpus

## Build unified KB
Run from `ai-service/`:

```bash
python kb/build_unified_kb.py --target-products 50
```

Outputs:
- `kb/unified_kb.json`: merged KB with provenance
- `kb/kb_chunks.json`: FAISS chunks payload
- `kb/neo4j_seed_payload.json`: graph ontology payload for Neo4j seeding

## Runtime usage
- `main.py` reads `kb/kb_chunks.json` for FAISS build/rebuild.
- `knowledge_graph/seed_neo4j.py` reads `kb/neo4j_seed_payload.json` for Symptom/Disease/Product/Category graph edges.
