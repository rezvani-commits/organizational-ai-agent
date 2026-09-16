from back.rag_graph import RAGGraph

rag = RAGGraph()

for step_update in rag.graph.stream(
    {
        "query": "سلام",
        "standalone_query": "",
        "was_rewritten": False,
        "session_id": "test-session",
        "parts": [],
        "is_multi_query": False,
        "sub_queries": [],
        "intent": "",
        "retrieved_docs": [],
        "context": "",
        "response": "",
        "validation_result": {},
        "retry_count": 0,
        "is_satisfied": False,
        "top_k": 3,
        "max_retries": 2,
    },
    stream_mode="updates",
):
    print("EVENT:", step_update)