# AI Service

This folder contains the standalone AI materials for the assignment.

## Structure
- `domain/`: category definitions and shared domain data
- `generate_user_behavior_data.py`: synthetic behavior data generator
- `preprocess_data.py`: feature engineering and sequence preparation
- `models.py`: RNN, LSTM, and BiLSTM builders
- `train_models.py`: model training and evaluation
- `select_best_model.py`: best-model selection by weighted F1
- `visualize_models.py`: comparison and training charts
- `knowledge_graph/`: Neo4j knowledge graph seeding and reporting
- `knowledge_graph_output/`: generated graph artifacts and summaries

## Run
From the `ai-service` folder:

```bash
python generate_user_behavior_data.py --output data_user500.csv
python train_models.py --data data_user500.csv --output artifacts_dataopt_seq8 --epochs 30 --seq-len 8 --learning-rate 0.0008 --batch-size 32
python select_best_model.py --artifacts artifacts_dataopt_seq8
python visualize_models.py --artifacts artifacts_dataopt_seq8
python knowledge_graph/run_knowledge_graph.py --data data_user500.csv --output knowledge_graph_output
```

## Outputs
- Dataset: `data_user500.csv`
- Model artifacts: `artifacts_dataopt_seq8/`
- Graph artifacts: `knowledge_graph_output/`

## Notes
- Category definitions live in `domain/category.py`.
- The knowledge graph folder is named without phase terms.
