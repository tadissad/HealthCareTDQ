# 📋 PLAN CHI TIẾT - AI SERVICE (BÀI TẬP LỚN)

**Deadline**: Tối thứ Hai 20/04 trước 11:30PM  
**File nộp**: `aiservice02_lớp.nhóm_tênho.PDF`  
**Tổng điểm**: 10 điểm (4 câu × 2.5 điểm)

---

## 🎯 TỔNG QUAN TASKS

| Phase | Task | Điểm | Deadline |
|-------|------|------|----------|
| **1** | 📊 Sinh dữ liệu `data_user500.csv` | 2đ | ASAP |
| **2** | 🤖 Xây dựng 3 mô hình (RNN/LSTM/biLSTM) | 2đ | Hôm nay |
| **3** | 📈 Xây dựng Knowledge Graph (Neo4j) | 2đ | Ngày mai |
| **4** | 💬 Xây dựng RAG + Chat | 2đ | Ngày mai |
| **5** | 🛒 Tích hợp vào e-commerce + UI | 2đ | Ngày kia |
| **6** | 📄 Chuẩn bị PDF nộp | - | 20/04 11:30PM |

---

## ✅ PHASE 1: SINH DỮ LIỆU (2 ĐIỂM)

### 📌 Mục tiêu
Tạo file `data_user500.csv` với 500 users + 8 behaviors

### 📋 Chi tiết công việc

#### 1.1 - Xác định cấu trúc dữ liệu
```
Columns: 8 cột
- user_id: ID người dùng (U001 - U500)
- product_id: ID sản phẩm (P001 - P100)
- action: hành động (view, click, add_to_cart, purchase, wishlist, review, share, compare)
- timestamp: thời gian hành động (2026-01-01 -> 2026-04-20)
- category: danh mục sản phẩm (ulcer_hp_support, reflux_heartburn, ...)
- price: giá sản phẩm (20000 - 500000 VND)
- rating: đánh giá (1-5 sao, nullable)
- session_duration: thời gian phiên (giây)
```

#### 1.2 - Tạo script sinh dữ liệu
```python
# File: generate_user_behavior_data.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_data_user500():
    """Sinh 500 users x 8 behaviors"""
    # 1. Random 500 users
    # 2. Random 100 products + categories
    # 3. Random 10 behaviors/user (tổng ~5000 records)
    # 4. Random timestamps
    # 5. Export CSV
    pass

if __name__ == '__main__':
    df = generate_data_user500()
    df.to_csv('data_user500.csv', index=False)
    print("✅ data_user500.csv created!")
    print(df.head(20))  # Show 20 dòng đầu
```

#### 1.3 - Validations
- ✅ File có 500 unique users
- ✅ 8 columns đúng
- ✅ ~5000 behavior records
- ✅ Timestamps hợp lệ
- ✅ Categories match với 10 categories mới

#### 1.4 - Deliverables (cho PDF)
- ✅ **Copy 20 dòng data** từ CSV
- ✅ **Screenshot** file CSV mở trong Excel
- ✅ **Code snippet** hàm sinh dữ liệu

---

## 🤖 PHASE 2: XÂY DỰNG 3 MÔ HÌNH ML (2 ĐIỂM)

### 📌 Mục tiêu
Xây dựng 3 mô hình RNN/LSTM/biLSTM để **dự đoán hành động tiếp theo** (predict next behavior)

### 📋 Chi tiết công việc

#### 2.1 - Chuẩn bị dữ liệu (Data Preprocessing)
```
Step 1: Load data_user500.csv
Step 2: Encode categorical columns
        - action → [view, click, add_to_cart, ...] → [0, 1, 2, ...]
        - category → [ulcer_hp_support, reflux_heartburn, ...] → [0, 1, ...]
Step 3: Create sequences
        - Sliding window: 5 behaviors → predict 6th behavior
        - User session sequences
        - Normalize prices (0-1)
Step 4: Train/Test split (80/20)
Step 5: Convert to numpy arrays for LSTM
```

**Code Structure:**
```python
# preprocess_data.py
def encode_actions(df):
    action_map = {'view': 0, 'click': 1, 'add_to_cart': 2, ...}
    return df

def create_sequences(data, seq_len=5):
    X, y = [], []
    for i in range(len(data) - seq_len):
        X.append(data[i:i+seq_len])
        y.append(data[i+seq_len])
    return np.array(X), np.array(y)
```

#### 2.2 - Xây dựng Model 1: RNN (Recurrent Neural Network)
```python
# models.py - Model 1
def build_rnn_model(seq_len, n_actions):
    model = Sequential([
        LSTM(64, input_shape=(seq_len, n_features), return_sequences=True),
        Dropout(0.2),
        SimpleRNN(32),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dense(n_actions, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model
```

**Hyperparameters:**
- Epochs: 50
- Batch size: 32
- Optimizer: Adam
- Loss: Categorical Crossentropy
- Metrics: Accuracy, Precision, Recall, F1

#### 2.3 - Xây dựng Model 2: LSTM (Long Short-Term Memory)
```python
# models.py - Model 2
def build_lstm_model(seq_len, n_actions):
    model = Sequential([
        LSTM(128, input_shape=(seq_len, n_features), return_sequences=True),
        Dropout(0.3),
        LSTM(64, return_sequences=False),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dense(n_actions, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model
```

#### 2.4 - Xây dựng Model 3: BiLSTM (Bidirectional LSTM)
```python
# models.py - Model 3
def build_bilstm_model(seq_len, n_actions):
    model = Sequential([
        Bidirectional(LSTM(128, input_shape=(seq_len, n_features), return_sequences=True)),
        Dropout(0.3),
        Bidirectional(LSTM(64)),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dense(n_actions, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model
```

#### 2.5 - Training & Evaluation
```python
# train_models.py
def train_all_models(X_train, y_train, X_test, y_test):
    models = {
        'RNN': build_rnn_model(...),
        'LSTM': build_lstm_model(...),
        'BiLSTM': build_bilstm_model(...)
    }
    
    results = {}
    for name, model in models.items():
        # Train
        history = model.fit(X_train, y_train, 
                           epochs=50, 
                           batch_size=32,
                           validation_split=0.2,
                           verbose=1)
        
        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, np.argmax(y_pred, axis=1))
        precision = precision_score(y_test, np.argmax(y_pred, axis=1), average='weighted')
        recall = recall_score(y_test, np.argmax(y_pred, axis=1), average='weighted')
        f1 = f1_score(y_test, np.argmax(y_pred, axis=1), average='weighted')
        
        results[name] = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'model': model,
            'history': history
        }
    
    return results
```

#### 2.6 - Visualization & Comparison
```python
# visualize_models.py
import matplotlib.pyplot as plt

def plot_comparison(results):
    metrics = ['accuracy', 'precision', 'recall', 'f1']
    models = list(results.keys())
    
    # Bar plot: So sánh 4 metrics
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    for idx, metric in enumerate(metrics):
        ax = axes[idx // 2, idx % 2]
        values = [results[m][metric] for m in models]
        ax.bar(models, values, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax.set_title(f'Model Comparison - {metric.upper()}')
        ax.set_ylim(0, 1)
        ax.set_ylabel(metric)
    
    plt.tight_layout()
    plt.savefig('model_comparison.png', dpi=300)
    plt.show()

def plot_training_history(results):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    for idx, (name, data) in enumerate(results.items()):
        history = data['history']
        axes[idx].plot(history.history['accuracy'], label='Train Acc')
        axes[idx].plot(history.history['val_accuracy'], label='Val Acc')
        axes[idx].set_title(f'{name} Training History')
        axes[idx].set_xlabel('Epoch')
        axes[idx].set_ylabel('Accuracy')
        axes[idx].legend()
    
    plt.tight_layout()
    plt.savefig('training_history.png', dpi=300)
    plt.show()
```

#### 2.7 - Chọn Model Tốt Nhất
```python
# select_best_model.py
def select_best_model(results):
    # Dùng F1 score để chọn (balance Precision/Recall)
    best_model_name = max(results, key=lambda x: results[x]['f1'])
    best_model = results[best_model_name]['model']
    
    print(f"✅ Best Model: {best_model_name}")
    print(f"   F1 Score: {results[best_model_name]['f1']:.4f}")
    print(f"   Accuracy: {results[best_model_name]['accuracy']:.4f}")
    
    # Save model
    best_model.save('model_best.h5')
    
    return best_model, best_model_name
```

#### 2.8 - Deliverables (cho PDF)
- ✅ **Code Câu 2a** (train_models.py + select_best_model.py)
- ✅ **Screenshot** 3 mô hình training
- ✅ **Bar chart** so sánh 4 metrics
- ✅ **Line chart** training history
- ✅ **Bảng kết quả** chi tiết
- ✅ **Lời giải thích** vì sao chọn model nào là tốt nhất

**Ví dụ bảng kết quả:**
```
┌────────┬──────────┬───────────┬─────────┬────────┐
│ Model  │ Accuracy │ Precision │ Recall  │ F1     │
├────────┼──────────┼───────────┼─────────┼────────┤
│ RNN    │ 0.7234   │ 0.7145    │ 0.7089  │ 0.7116 │
│ LSTM   │ 0.8456   │ 0.8389    │ 0.8412  │ 0.8400 │
│ BiLSTM │ 0.8623   │ 0.8567    │ 0.8598  │ 0.8582 │
└────────┴──────────┴───────────┴─────────┴────────┘

✅ Chọn: BiLSTM (F1 cao nhất = 0.8582)
Lý do: BiLSTM học từ 2 hướng → capture dependencies tốt hơn
```

---

## 📈 PHASE 3: KNOWLEDGE GRAPH VỚI NEO4J (2 ĐIỂM)

### 📌 Mục tiêu
Xây dựng Knowledge Graph từ data_user500.csv, visualize bằng Neo4j

### 📋 Chi tiết công việc

#### 3.1 - Thiết kế Graph Schema
```
Nodes:
├─ User (user_id, name, email)
├─ Product (product_id, name, price, category)
├─ Action (type: view, click, add_to_cart, purchase, wishlist, review, share, compare)
├─ Category (category_id, name)
├─ Review (rating, text, timestamp)
└─ Session (session_id, start_time, end_time, duration)

Relationships:
├─ User -[:PERFORMS]-> Action
├─ Action -[:ON_PRODUCT]-> Product
├─ Product -[:BELONGS_TO]-> Category
├─ User -[:VIEWED]-> Product
├─ User -[:ADDED_TO_CART]-> Product
├─ User -[:PURCHASED]-> Product
├─ User -[:WROTE_REVIEW]-> Review
├─ Review -[:FOR_PRODUCT]-> Product
├─ User -[:IN_SESSION]-> Session
└─ Product -[:SIMILAR_TO]-> Product (dựa trên co-purchase)
```

#### 3.2 - Chuẩn bị dữ liệu cho Neo4j
```python
# neo4j_seed.py
from neo4j import GraphDatabase

def seed_knowledge_graph(csv_file):
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "health123"))
    
    # 1. Create Users from unique user_ids
    # 2. Create Products from unique product_ids
    # 3. Create Categories
    # 4. Create Actions/Relationships
    # 5. Create Sessions
    # 6. Calculate Product Similarities
    
    with driver.session() as session:
        # Xóa dữ liệu cũ
        session.run("MATCH (n) DETACH DELETE n")
        
        # Tạo constraints (unique)
        session.run("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE")
        session.run("CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE")
        session.run("CREATE CONSTRAINT category_id IF NOT EXISTS FOR (c:Category) REQUIRE c.category_id IS UNIQUE")
        
        # Import data từ CSV + tạo relationships
        df = pd.read_csv(csv_file)
        
        for idx, row in df.iterrows():
            # Create User
            session.run("""
                MERGE (u:User {user_id: $uid})
                ON CREATE SET u.name = $uname, u.created_at = datetime()
            """, uid=row['user_id'], uname=f"User_{row['user_id']}")
            
            # Create Product + Category
            session.run("""
                MERGE (c:Category {name: $cat})
                MERGE (p:Product {product_id: $pid})
                ON CREATE SET p.name = $pname, p.price = $price, p.created_at = datetime()
                MERGE (p)-[:BELONGS_TO]->(c)
            """, cat=row['category'], pid=row['product_id'], pname=f"Product_{row['product_id']}", price=row['price'])
            
            # Create Action
            session.run("""
                MATCH (u:User {user_id: $uid})
                MATCH (p:Product {product_id: $pid})
                CREATE (u)-[:PERFORMS {action_type: $action, timestamp: $ts}]->(p)
            """, uid=row['user_id'], pid=row['product_id'], action=row['action'], ts=row['timestamp'])
    
    driver.close()
    print("✅ Knowledge Graph seeded!")
```

#### 3.3 - Queries thú vị
```cypher
-- Query 1: Top 10 products by views
MATCH (u:User)-[r:PERFORMS {action_type: 'view'}]->(p:Product)
RETURN p.product_id, p.name, COUNT(r) as view_count
ORDER BY view_count DESC LIMIT 10

-- Query 2: User co-purchase patterns
MATCH (u:User)-[:PERFORMS {action_type: 'purchase'}]->(p1:Product)
MATCH (u)-[:PERFORMS {action_type: 'purchase'}]->(p2:Product)
WHERE p1 <> p2
RETURN p1.product_id, p2.product_id, COUNT(*) as co_purchase_count
ORDER BY co_purchase_count DESC LIMIT 20

-- Query 3: Products in same category
MATCH (p1:Product)-[:BELONGS_TO]->(c:Category)<-[:BELONGS_TO]-(p2:Product)
WHERE p1 <> p2
RETURN p1.product_id, p2.product_id, c.name
LIMIT 15

-- Query 4: User journey
MATCH (u:User {user_id: 'U001'})-[r:PERFORMS]->(p:Product)
RETURN u.user_id, r.action_type, p.product_id, r.timestamp
ORDER BY r.timestamp
LIMIT 20
```

#### 3.4 - Visualization
```python
# visualize_neo4j.py
import json
from py2neo import Graph

def export_graph_as_json(neo4j_uri, user, password):
    graph = Graph(neo4j_uri, auth=(user, password))
    
    # Export nodes
    nodes_query = "MATCH (n) RETURN id(n) as id, labels(n) as labels, properties(n) as props LIMIT 100"
    nodes = graph.run(nodes_query).data()
    
    # Export relationships
    edges_query = "MATCH (a)-[r]->(b) RETURN id(a) as source, id(b) as target, type(r) as type, properties(r) as props LIMIT 200"
    edges = graph.run(edges_query).data()
    
    # Format cho D3.js visualization
    data = {
        "nodes": [{"id": n['id'], "label": n['labels'][0], "title": str(n['props'])} for n in nodes],
        "links": [{"source": e['source'], "target": e['target'], "type": e['type']} for e in edges]
    }
    
    with open('graph_data.json', 'w') as f:
        json.dump(data, f)
    
    return data
```

#### 3.5 - HTML Visualization
```html
<!-- graph_visualization.html -->
<!DOCTYPE html>
<html>
<head>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body { font: 12px sans-serif; }
        svg { border: 1px solid #ccc; }
        .node { stroke: #fff; stroke-width: 1.5px; }
        .link { stroke: #999; stroke-opacity: 0.6; }
    </style>
</head>
<body>
    <svg width="800" height="600"></svg>
    <script>
        // Load graph_data.json
        // Render D3 force-directed graph
    </script>
</body>
</html>
```

#### 3.6 - Deliverables (cho PDF)
- ✅ **Screenshot Neo4j Browser** - 20 nodes/edges
- ✅ **Graph visualization** (D3.js hoặc Cypher result)
- ✅ **Schema diagram** (nodes + relationships)
- ✅ **Top 5 queries + results**
- ✅ **Graph statistics**:
  - Total nodes: X
  - Total relationships: Y
  - Density: Z

**Ví dụ:**
```
📊 Knowledge Graph Statistics:
├─ Total Users: 500
├─ Total Products: 100
├─ Total Categories: 10
├─ Total Actions: 5,234
├─ Total Relationships: 7,832
└─ Graph Density: 0.234
```

---

## 💬 PHASE 4: RAG + CHAT (2 ĐIỂM)

### 📌 Mục tiêu
Xây dựng Retrieval Augmented Generation (RAG) dựa trên KB_Graph + Gemini API

### 📋 Chi tiết công việc

#### 4.1 - Tạo Vector Store (FAISS)
```python
# rag_setup.py
from sentence_transformers import SentenceTransformer
import faiss
import pickle

def create_vector_store():
    # 1. Extract knowledge từ Neo4j
    # 2. Embed mỗi knowledge chunk
    # 3. Lưu vào FAISS
    
    model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
    
    # Knowledge chunks từ Neo4j
    knowledge_chunks = [
        "Phosphalugel là thuốc kháng acid bảo vệ niêm mạc dạ dày",
        "Nexium 20mg là thuốc ức chế bơm proton (PPI)",
        "Lacidofil là probiotic y tế với Lactobacillus sống",
        # ... 100+ more chunks từ products/categories
    ]
    
    # Encode
    embeddings = model.encode(knowledge_chunks, convert_to_tensor=True)
    
    # Create FAISS index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings).astype('float32'))
    
    # Save
    faiss.write_index(index, 'knowledge.index')
    with open('knowledge_chunks.pkl', 'wb') as f:
        pickle.dump(knowledge_chunks, f)
    
    print("✅ Vector store created!")
```

#### 4.2 - RAG Retrieval
```python
# rag_retriever.py
class RAGRetriever:
    def __init__(self):
        self.model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        self.index = faiss.read_index('knowledge.index')
        with open('knowledge_chunks.pkl', 'rb') as f:
            self.chunks = pickle.load(f)
    
    def retrieve(self, query, top_k=5):
        # Embed query
        query_embedding = self.model.encode([query])[0]
        
        # Search top-k similar chunks
        distances, indices = self.index.search(
            np.array([query_embedding]).astype('float32'), 
            top_k
        )
        
        # Return relevant chunks
        results = [
            {
                'chunk': self.chunks[idx],
                'score': 1 / (1 + dist)  # Convert distance to similarity
            }
            for idx, dist in zip(indices[0], distances[0])
        ]
        
        return results
```

#### 4.3 - Chat with Gemini
```python
# chat_service.py
from google import genai

class ChatService:
    def __init__(self):
        self.client = genai.Client(api_key="YOUR_GEMINI_API_KEY")
        self.retriever = RAGRetriever()
        self.conversation_history = []
    
    def chat(self, user_message):
        # 1. Retrieve relevant context
        context = self.retriever.retrieve(user_message)
        context_text = "\n".join([c['chunk'] for c in context])
        
        # 2. Build prompt
        system_prompt = """Bạn là AI tư vấn sức khỏe cho hệ e-commerce y tế.
        Dựa trên kiến thức sau, trả lời câu hỏi của user:
        
        KNOWLEDGE BASE:
        {context_text}
        """
        
        # 3. Generate response
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                {
                    "role": "user",
                    "parts": [user_message + "\n\nContext: " + context_text]
                }
            ],
            system_instruction=system_prompt
        )
        
        ai_message = response.text
        
        # 4. Store in history
        self.conversation_history.append({
            'role': 'user',
            'message': user_message,
            'context_used': context
        })
        self.conversation_history.append({
            'role': 'assistant',
            'message': ai_message
        })
        
        return ai_message
```

#### 4.4 - Chat Interface
```python
# chat_ui.py (Flask/Streamlit)
import streamlit as st

st.title("💬 AI Health Consultant")
st.write("Tư vấn sức khỏe từ hệ thống e-commerce y tế")

chat_service = ChatService()

# Chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display history
for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.write(message['content'])

# Input
user_input = st.chat_input("Nhập câu hỏi...")
if user_input:
    # User message
    st.session_state.messages.append({
        'role': 'user',
        'content': user_input
    })
    
    # AI response
    ai_response = chat_service.chat(user_input)
    st.session_state.messages.append({
        'role': 'assistant',
        'content': ai_response
    })
    
    st.rerun()
```

#### 4.5 - Deliverables (cho PDF)
- ✅ **Architecture diagram** (Query → Retrieval → Generation)
- ✅ **Code: RAG Retriever + Chat Service**
- ✅ **Screenshot** chat interface
- ✅ **Example conversations** (5-10 examples)
- ✅ **Performance metrics**:
  - Average retrieval time
  - Vector store size
  - Top-k accuracy

---

## 🛒 PHASE 5: TÍCH HỢP VÀO E-COMMERCE (2 ĐIỂM)

### 📌 Mục tiêu
Tích hợp models + KB_Graph + RAG vào hệ thống health-micro-ai

### 📋 Chi tiết công việc

#### 5.1 - Product Recommendation (Sử dụng best_model.h5)
```python
# recommendation_service.py
from tensorflow.keras.models import load_model

class RecommendationService:
    def __init__(self):
        self.model = load_model('model_best.h5')
        self.encoder = ActionEncoder()
    
    def recommend_next_product(self, user_id):
        """Dự đoán hành động tiếp theo của user"""
        # 1. Get user's last 5 actions
        user_actions = get_user_recent_actions(user_id, limit=5)
        
        # 2. Encode actions
        X = self.encoder.encode(user_actions)
        X = np.array([X])
        
        # 3. Predict next action
        y_pred = self.model.predict(X)
        next_action_prob = y_pred[0]
        
        # 4. If next action is 'view' or 'click', recommend products
        if next_action_prob[0] > 0.7:  # 70% likely to view/click
            # Query Neo4j for top similar products
            similar_products = query_similar_products(user_id, top_k=5)
            return similar_products
        
        return None
```

#### 5.2 - Search Augmentation
```python
# search_service.py
def augmented_search(query):
    """Search + RAG + Recommendation"""
    # 1. Traditional search
    results = traditional_search(query)
    
    # 2. Add RAG context
    rag_context = retriever.retrieve(query, top_k=3)
    
    # 3. Re-rank results
    ranked_results = rerank_products(results, rag_context)
    
    return ranked_results
```

#### 5.3 - Cart Augmentation
```python
# cart_service.py
def get_cart_recommendations(user_id):
    """Khi user click vào giỏ hàng → show recommendations"""
    cart_items = get_user_cart(user_id)
    
    # 1. Get co-purchase patterns từ Neo4j
    recommendations = query_copurchase_products(
        product_ids=[item['product_id'] for item in cart_items],
        top_k=5
    )
    
    # 2. Filter by price range
    recommendations = filter_by_price_range(recommendations, max_price=500000)
    
    # 3. Rank by popularity
    recommendations = rank_by_popularity(recommendations)
    
    return recommendations
```

#### 5.4 - Frontend Integration (Django Template)

**Search Results:**
```html
<!-- templates/search_results.html -->
<div class="search-results">
    <div class="ai-insight">
        <h3>💡 AI Gợi Ý</h3>
        <p>{{ rag_context }}</p>
    </div>
    
    <div class="products">
        {% for product in products %}
            <div class="product-card">
                <h4>{{ product.name }}</h4>
                <p>Giá: {{ product.price }}</p>
                <button onclick="addToCart({{ product.id }})">Thêm vào giỏ</button>
            </div>
        {% endfor %}
    </div>
</div>
```

**Cart View:**
```html
<!-- templates/cart.html -->
<div class="cart">
    <h2>🛒 Giỏ Hàng</h2>
    
    <div class="cart-items">
        {% for item in cart_items %}
            <!-- Show items -->
        {% endfor %}
    </div>
    
    <div class="ai-recommendations">
        <h3>🎯 Sản phẩm liên quan</h3>
        {% for rec in recommendations %}
            <div class="rec-card">
                <img src="{{ rec.image }}" />
                <h4>{{ rec.name }}</h4>
                <p>{{ rec.description }}</p>
                <button>Thêm</button>
            </div>
        {% endfor %}
    </div>
</div>
```

**Chat Interface:**
```html
<!-- templates/ai_chat.html -->
<div class="chat-container">
    <div class="chat-header">
        <h2>💬 Tư vấn AI Sức Khỏe</h2>
    </div>
    
    <div class="chat-messages" id="chatMessages">
        <!-- Messages dynamically added -->
    </div>
    
    <div class="chat-input">
        <input type="text" id="userInput" placeholder="Nhập câu hỏi...">
        <button onclick="sendMessage()">Gửi</button>
    </div>
</div>

<script>
async function sendMessage() {
    const message = document.getElementById('userInput').value;
    
    // Add user message to UI
    addMessageToUI('user', message);
    
    // Call AI service
    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: message})
    });
    
    const data = await response.json();
    
    // Add AI response to UI
    addMessageToUI('assistant', data.response);
    
    // Show products if recommended
    if (data.products) {
        showProductRecommendations(data.products);
    }
}
</script>
```

#### 5.5 - API Endpoints
```python
# views.py (Django)

@api_view(['GET'])
def search_products(request):
    """GET /api/products/search?q=viêm loét"""
    query = request.GET.get('q')
    results = augmented_search(query)
    return Response(results)

@api_view(['GET'])
def cart_recommendations(request):
    """GET /api/cart/recommendations"""
    user_id = request.user.id
    recs = get_cart_recommendations(user_id)
    return Response(recs)

@api_view(['POST'])
def chat_message(request):
    """POST /api/chat"""
    message = request.data.get('message')
    user_id = request.user.id
    
    response = chat_service.chat(message)
    products = extract_product_mentions(response)
    
    return Response({
        'response': response,
        'products': products
    })

@api_view(['GET'])
def recommendations(request):
    """GET /api/recommendations"""
    user_id = request.user.id
    recs = recommendation_service.recommend_next_product(user_id)
    return Response(recs)
```

#### 5.6 - Deliverables (cho PDF)
- ✅ **Architecture diagram** (tích hợp models + KB_Graph + RAG)
- ✅ **Screenshots**: 
  - Search results with AI insights
  - Cart with recommendations
  - Chat interface
- ✅ **Code snippets**: recommendation_service.py + search_service.py
- ✅ **API documentation**
- ✅ **User flow diagram**

---

## 📄 PHASE 6: CHUẨN BỊ PDF NỘP

### 📋 Cấu trúc PDF

```
1. TRANG BÌA
   - Tiêu đề: "AI SERVICE - E-Commerce Y Tế"
   - Lớp + Nhóm + Tên học sinh
   - Ngày nộp: 20/04/2026
   - Logo trường

2. MỤC LỤC

3. PHẦN 1: MỐ TẢ AISERVICE (1 trang)
   - Tổng quan hệ thống
   - 5 components chính
   - Tích hợp cách nào

4. PHẦN 2A: DỮ LIỆU (1 trang)
   - Copy 20 dòng data_user500.csv (bảng)
   - Screenshot file CSV
   - Thống kê: 500 users, 8 behaviors, 5000+ records

5. PHẦN 2B: MÔ HÌNH ML (3-4 trang)
   - Code: train_models.py + select_best_model.py
   - 3 screenshots: RNN, LSTM, BiLSTM training
   - Bảng so sánh metrics
   - 2-3 charts: comparison + training history
   - Lời giải thích: Why BiLSTM best? (vì bidirectional capture better)

6. PHẦN 2C: KNOWLEDGE GRAPH (2-3 trang)
   - Neo4j schema diagram
   - Screenshot Neo4j Browser (20 nodes/edges)
   - Graph visualization (D3.js)
   - Top 3 Cypher queries + results

7. PHẦN 2D: RAG + CHAT (2 trang)
   - Architecture diagram
   - Code: rag_setup.py + chat_service.py
   - Screenshot chat UI
   - 3 example conversations
   - Performance metrics

8. PHẦN 2E: TÍCH HỢP E-COMMERCE (2-3 trang)
   - System architecture
   - 3 screenshots: search, cart, chat
   - Code: recommendation_service.py
   - API endpoints documentation
   - User journey diagram

9. KẾT LUẬN & HƯỚNG PHÁT TRIỂN (1 trang)
   - Kết quả đạt được
   - Thách thức gặp phải
   - Hướng phát triển tiếp theo

10. TÀI LIỆU THAM KHẢO
```

### 📋 Checklist Nội Dung

- ✅ 20 dòng data CSV
- ✅ Code Câu 2a (RNN/LSTM/biLSTM)
- ✅ 5+ screenshots từ training
- ✅ 2+ charts/graphs so sánh models
- ✅ Neo4j screenshot (20 nodes/edges)
- ✅ Graph visualization
- ✅ Cypher queries
- ✅ RAG code + screenshots
- ✅ Chat interface screenshot
- ✅ Search/Cart screenshots
- ✅ Lời giải thích cho từng phần

---

## ⏰ TIMELINE CHI TỈ

| Ngày | Task | Status |
|------|------|--------|
| 20/04 (Hôm nay) | Phase 1 + Phase 2 | 🔴 TODO |
| 21/04 | Phase 3 + Phase 4 | 🔴 TODO |
| 22/04 | Phase 5 | 🔴 TODO |
| 23/04 | PDF chuẩn bị + review | 🔴 TODO |
| 24/04 | Nộp trước 11:30PM | 🔴 DEADLINE |

---

## 🛠️ TOOLS & LIBRARIES CẦN

```
# Python
pip install pandas numpy scikit-learn tensorflow keras
pip install neo4j py2neo sentence-transformers faiss-cpu
pip install google-genai streamlit flask matplotlib seaborn
pip install requests beautifulsoup4

# Database
- PostgreSQL (Django ORM)
- Neo4j (Knowledge Graph)
- FAISS (Vector Store)

# APIs
- Gemini API (Google)
```

---

## 📝 NOTES QUAN TRỌNG

1. **Chú ý yêu cầu đặc biệt**:
   - Copy 20 dòng data (không phải 10 hay 15)
   - Ảnh graph "càng phức tạp-đẹp càng có giá trị"
   - Chat UI "không phải giao diện thường của ChatGPT"
   - Lưu file trên máy (không upload mây)

2. **Lời giải thích**:
   - Phải giải thích WHY chọn model nào tốt nhất
   - Graph structure tại sao thiết kế vậy
   - RAG hoạt động thế nào

3. **Formatting PDF**:
   - Font rõ ràng (Arial hoặc Calibri)
   - Ảnh đủ lớn (readable)
   - Code có syntax highlighting
   - Bảng được format đẹp

4. **Quality**:
   - Không copy-paste từ internet
   - Phải run được trên máy
   - Có comments trong code

---

## ✅ FINAL CHECKLIST TRƯỚC KHI NỘP

- [ ] Tất cả 5 phases đã complete
- [ ] PDF có đủ 10 sections
- [ ] 20 dòng data trong PDF
- [ ] Code Câu 2a + 2b + 2c + 2d trong PDF
- [ ] 10+ screenshots chất lượng cao
- [ ] 3+ charts/graphs visualization
- [ ] Lời giải thích rõ ràng cho từng phần
- [ ] File PDF có tên đúng format: `aiservice02_lớp.nhóm_tênho.PDF`
- [ ] Toàn bộ source code lưu trên máy
- [ ] Test chạy thử tất cả services
- [ ] PDF có dung lượng < 50MB (nếu có images)

---

**Bắt đầu ngay từ Phase 1 để có đủ thời gian! 💪**
