# Deployment Folder

This folder contains all files needed to deploy the Cysterhood PCOS RAG application.

## Essential Files

- `app.py` - Main Streamlit application
- `query_rag.py` - RAG chain and retrieval logic
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python version specification (3.11)
- `pcos_papers_merged.csv` - Research papers dataset
- `all_patient_articles_text_only.json` - Patient-friendly articles
- `chroma_pcos_db_semantic/` - Vector database for research papers
- `chroma_patient_db/` - Vector database for patient articles
- `assets/` - Logo and images
- `.streamlit/config.toml` - Streamlit configuration

## Deployment

See `../DEPLOY_EXTERNAL.md` for deployment instructions to Streamlit Cloud, Railway, Render, or other platforms.
