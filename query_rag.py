import os
import json
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel
import pandas as pd
import requests

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_anthropic import ChatAnthropic
from sentence_transformers import CrossEncoder

load_dotenv()


class QueryVariations(BaseModel):
    queries: List[str]


# ---------- Helpers to reload docs for BM25 ----------


def load_and_clean_papers_for_bm25(csv_path: str) -> List[Document]:
    print(f"📄 [BM25] Loading papers from: {csv_path}")
    df = pd.read_csv(csv_path)
    df = df[df["abstract"].notna() | df["fulltext"].notna()]

    docs: List[Document] = []
    for _, row in df.iterrows():
        if pd.notna(row["abstract"]):
            docs.append(
                Document(
                    page_content=row["abstract"],
                    metadata={
                        "title": row["title"],
                        "year": row["year"],
                        "chunk_type": "abstract",
                        "source": "Research",
                    },
                )
            )
        if pd.notna(row["fulltext"]):
            docs.append(
                Document(
                    page_content=row["fulltext"],
                    metadata={
                        "title": row["title"],
                        "year": row["year"],
                        "chunk_type": "fulltext",
                        "source": "Research",
                    },
                )
            )
    print(f"📝 [BM25] Created {len(docs)} research docs")
    return docs


def load_patient_articles_for_bm25(json_path: str) -> List[Document]:
    print(f"📄 [BM25] Loading patient articles from: {json_path}")
    with open(json_path, "r") as f:
        raw_data = json.load(f)

    docs: List[Document] = []
    for entry in raw_data:
        content = entry["text"]
        metadata = {
            "source": entry.get("source", "Patient"),
            "title": entry.get("title", "Untitled"),
            "id": entry.get("id", None),
            "chunk_type": "patient",
        }
        docs.append(Document(page_content=content, metadata=metadata))
    print(f"📝 [BM25] Loaded {len(docs)} patient docs")
    return docs


# ---------- Hybrid retrievers (MMR + BM25 + ensemble) ----------


def build_retrievers(include_patient_data: bool = True):
    print("📂 Loading vectorstores...")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    main_store = Chroma(
        persist_directory="./chroma_pcos_db_semantic",
        embedding_function=embeddings,
    )
    # MMR-based vector retriever
    main_vector_retriever = main_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5, "fetch_k": 20, "lambda_mult": 0.5},
    )

    if include_patient_data:
        patient_store = Chroma(
            persist_directory="./chroma_patient_db",
            embedding_function=embeddings,
        )
        patient_vector_retriever = patient_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 20, "lambda_mult": 0.5},
        )

        print("🔗 Using dual corpora (research + patient)")
        print("🧮 Building BM25 retrievers from original docs...")

        research_docs = load_and_clean_papers_for_bm25(
            "pcos_papers_merged.csv"
        )
        main_bm25 = BM25Retriever.from_documents(research_docs)
        main_bm25.k = 5

        patient_docs = load_patient_articles_for_bm25(
            "all_patient_articles_text_only.json"
        )
        patient_bm25 = BM25Retriever.from_documents(patient_docs)
        patient_bm25.k = 5

        main_hybrid = EnsembleRetriever(
            retrievers=[main_vector_retriever, main_bm25],
            weights=[0.7, 0.3],
        )
        patient_hybrid = EnsembleRetriever(
            retrievers=[patient_vector_retriever, patient_bm25],
            weights=[0.7, 0.3],
        )

        return [main_hybrid, patient_hybrid]

    print("🧮 Building BM25 retriever from research docs...")
    research_docs = load_and_clean_papers_for_bm25("pcos_papers_merged.csv")
    main_bm25 = BM25Retriever.from_documents(research_docs)
    main_bm25.k = 5

    main_hybrid = EnsembleRetriever(
        retrievers=[main_vector_retriever, main_bm25],
        weights=[0.7, 0.3],
    )

    return [main_hybrid]


def retrieve_combined(retrievers: List, query: str) -> List:
    results = []
    for r in retrievers:
        results.extend(r.invoke(query))
    seen = set()
    unique = []
    for d in results:
        sig = (d.page_content, tuple(sorted(d.metadata.items())))
        if sig not in seen:
            seen.add(sig)
            unique.append(d)
    return unique[:10]


def fallback_web_search(query: str) -> List[str]:
    print("🌐 Triggering real-time web search fallback...")
    api_key = os.getenv("BING_API_KEY")
    if not api_key:
        print("❌ BING_API_KEY not set.")
        return []

    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {
        "q": query,
        "count": 5,
        "textDecorations": True,
        "textFormat": "HTML",
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print("❌ Web search failed:", response.text)
        return []

    data = response.json()
    snippets: List[str] = []
    for result in data.get("webPages", {}).get("value", []):
        snippets.append(
            f"{result['name']} ({result['url']}): {result['snippet']}"
        )
    return snippets


def format_docs(docs: List) -> str:
    return "\n\n".join(
        f"[{d.metadata.get('title', 'N/A')} - {d.metadata.get('source', 'N/A')}]:\n{d.page_content}"
        for d in docs
    )


def generate_query_variations(llm: ChatAnthropic, question: str) -> List[str]:
    prompt = (
        "Generate 3 different variations of this user question to help retrieve relevant documents.\n\n"
        f"Original question: {question}\n\n"
        "Return each variation on a new line without numbering or bullets."
    )
    resp = llm.invoke(prompt)
    raw = resp.content.strip()
    variations = [line.strip() for line in raw.split("\n") if line.strip()]
    return variations[:3]


def create_rag_chain(
    retrievers: List,
    use_multiquery: bool = False,
    use_rerank: bool = False,
):
    print("⚙️ Setting up RAG chain...")
    llm = ChatAnthropic(model="claude-3-haiku-20240307")

    reranker = (
        CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2") if use_rerank else None
    )

    prompt = PromptTemplate.from_template(
        """You are a PCOS education assistant. Use the following research and patient-friendly excerpts to answer the question in clear, empathetic language.

Context:
{context}

Question: {question}

Instructions:
- Explain in simple, patient-friendly terms
- Cite the source title or year when referencing specific findings
- If the information is not in the context, say so rather than making things up
- Break down complex medical terms

Answer:"""
    )

    def chain_call(question: str, history: List[str]):
        print(f"\n🔍 Retrieving documents for: {question}")

        if use_multiquery:
            print("🔁 Generating query variations (no structured_output)...")
            queries = generate_query_variations(llm, question)
            print("Generated variations:")
            for q in queries:
                print(f" - {q}")
            docs = []
            for q in queries:
                docs.extend(retrieve_combined(retrievers, q))
            # Deduplicate across all query variations
            seen = set()
            unique_docs = []
            for d in docs:
                sig = (d.page_content, tuple(sorted(d.metadata.items())))
                if sig not in seen:
                    seen.add(sig)
                    unique_docs.append(d)
            docs = unique_docs
        else:
            docs = retrieve_combined(retrievers, question)

        if len(docs) < 2:
            print("⚠️ Low recall — using web search fallback")
            snippets = fallback_web_search(question)
            docs = [
                type(
                    "Doc",
                    (),
                    {
                        "page_content": s,
                        "metadata": {"title": "Web", "source": "Bing"},
                    },
                )
                for s in snippets
            ]

        if reranker and docs:
            print("🎯 Reranking results with CrossEncoder...")
            pairs = [(question, d.page_content) for d in docs]
            scores = reranker.predict(pairs)
            docs = [
                doc
                for doc, _ in sorted(
                    zip(docs, scores), key=lambda x: x[1], reverse=True
                )
            ]

        context = format_docs(docs[:5])
        response = llm.invoke(prompt.format(context=context, question=question))
        history.append(f"Q: {question}\nA: {response.content}")
        return response.content, docs

    print("✅ RAG chain ready (hybrid + MMR + rerank capable)")
    return chain_call


def query_pcos_rag(chain_call, questions: List[str]):
    history: List[str] = []
    for question in questions:
        print(f"\n🧠 QUESTION: {question}")
        answer, docs = chain_call(question, history)
        print("\n💬 ANSWER:\n", answer)
        print("\n📚 SOURCES:")
        for i, doc in enumerate(docs[:3]):
            print(
                f"{i+1}. {doc.metadata.get('title', 'N/A')} - {doc.metadata.get('source', 'N/A')}"
            )
    print("\n🗂️ CHAT HISTORY:")
    for turn in history:
        print("\n" + turn)


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY not set.")
    retrievers = build_retrievers(include_patient_data=True)
    chain_call = create_rag_chain(
        retrievers,
        use_multiquery=True,
        use_rerank=True,
    )
    query_pcos_rag(
        chain_call,
        [
            "What causes insulin resistance in PCOS?",
            "What are the best treatments for PCOS hirsutism?",
            "How does metformin help with PCOS?",
            "What lifestyle changes help manage PCOS?",
        ],
    )
