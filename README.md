# Wikipedia Search Engine

A high-performance search engine for English Wikipedia, built as part of the Information Retrieval course (372-1-4406).

## Project Overview

This search engine processes and retrieves results from the entire English Wikipedia corpus (6.3M+ documents) using multiple ranking signals including BM25, TF-IDF, PageRank, and PageViews. 

**Final Results Quality Score: 0.356** (154% improvement over baseline)

---

## Team

| Student ID | Email |
|------------|-------|
| [ID 1] | [email1@post.bgu.ac.il] |
| [ID 2] | [email2@post.bgu.ac.il] |

---

## Repository Structure

```
📁 Root
├── 📄 search_frontend.py          # Flask app - main entry point
├── 📄 backend.py                  # Core search logic and ranking
├── 📄 inverted_index_gcp.py       # Inverted index for GCP
├── 📄 engin.py                    # Engine utilities
│
├── 📁 Index Building Notebooks
│   ├── 📓 body_nostem_Index.ipynb           # Body index (no stemming)
│   ├── 📓 Body_Index_Stemming.ipynb         # Body index with stemming
│   ├── 📓 Body_Index_With_Phrases_.ipynb    # Body index with phrases
│   ├── 📓 Build_Title_Index_NoStemming.ipynb
│   ├── 📓 Build_AnchorText_Index_GCP.ipynb
│   ├── 📓 anchor_index_gcp.ipynb
│   ├── 📓 Build_PageRank_GCP.ipynb
│   ├── 📓 Page_Views.ipynb
│   ├── 📓 pmi_phrase_index.ipynb
│   └── 📓 Phrases_inverted_Index_body.ipynb
│
├── 📓 run_frontend_in_colab__1_.ipynb   # Development notebook
├── 📄 queries_train.json                # Training queries
└── 📄 pageviews-202108-user-4dedup.txt  # PageView data
```

---

## System Architecture

### Indexing Components

| Index | GCS Location | Purpose |
|-------|--------------|---------|
| Body (No Stem) | `postings_gcp/` | TF-IDF cosine similarity |
| Body (Stemmed) | `body_stemmed_phrases/` | BM25 ranking |
| Title | `title_nostem/` | Binary title matching |
| Anchor | `anchor_postings_gcp/` | Anchor text ranking |
| PageRank | `pr/` | Link authority scores |
| PageViews | `page_views/` | Popularity data |

### Ranking Weights

| Signal | Weight | Description |
|--------|--------|-------------|
| Body (BM25) | **1.7** | Full-text relevance |
| Title (IDF) | **0.95** | Title matching |
| Anchor | **0.45** | Anchor text analysis |
| PageRank | **0.4** | Authority score |
| PageViews | **0.5** | Popularity |

---

## API Endpoints

### GET Endpoints

| Endpoint | Description |
|----------|-------------|
| `/search?query=...` | Main search - returns top 100 results |
| `/search_body?query=...` | TF-IDF cosine similarity on body |
| `/search_title?query=...` | Binary ranking by title |
| `/search_anchor?query=...` | Binary ranking by anchor text |

### POST Endpoints

| Endpoint | Description |
|----------|-------------|
| `/get_pagerank` | Returns PageRank for list of doc IDs |
| `/get_pageview` | Returns page views for list of doc IDs |

---

## Performance

### Results Quality Progression

| Version | RQ Score | Changes |
|---------|----------|---------|
| v1 (Baseline) | 0.14 | Body search only |
| v2 | 0.18 | Added title search |
| v3 | 0.25 | Multi-signal fusion |
| v4 | 0.31 | Weight optimization |
| **v5 (Final)** | **0.356** | Bug fix (top-k selection) |

### Efficiency

- ⚡ Average query time: **< 2 seconds**
- ✅ All queries complete within 35 second limit
- 🔧 Optimized posting list reading with caching

---

## Algorithms

### BM25 (Body Search)

```
score(D,Q) = Σ IDF(qi) × (tf × (k1+1)) / (tf + k1 × (1 - b + b × |D|/avgdl))
```

**Parameters:** k1 = 1.5, b = 0.75

### Score Fusion

```
final_score = 1.7×body + 0.95×title + 0.45×anchor + 0.4×pagerank + 0.5×pageview
```

---

## Setup & Deployment

### Prerequisites

- Python 3.8+
- Google Cloud SDK
- Access to GCS bucket `db204905756`

### Local Development (Colab)

1. Upload required files to Colab:
   - `backend.py`
   - `search_frontend.py`
   - `inverted_index_gcp.py`

2. Run the notebook: `run_frontend_in_colab__1_.ipynb`

### GCP Deployment

Follow instructions in `run_frontend_in_gcp.sh`:
1. Create Compute Engine instance
2. Reserve static IP
3. Deploy search engine

---

## GCS Bucket

**Bucket:** `gs://db204905756/`

### Index Files

```
gs://db204905756/
├── postings_gcp/           # Body index
├── body_stemmed_phrases/   # Stemmed body index
├── title_nostem/           # Title index
├── anchor_postings_gcp/    # Anchor index
├── pr/                     # PageRank scores
├── page_views/             # PageView data
└── id_title/               # Doc ID to title mapping
```

---

## Key Learnings

1. **Top-K vs Random Sampling** - Critical bug: always sort by score before selecting top results
2. **Multi-Signal Ranking** - Combining signals significantly outperforms single-signal approaches
3. **Weight Tuning** - Empirical tuning beats theoretical assumptions
4. **Query-Specific Features** - Anchor text analysis provides substantial improvements

---

## License

Educational project for BGU's Information Retrieval course (2024-2025).
