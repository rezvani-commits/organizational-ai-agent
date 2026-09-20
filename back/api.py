from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from back.rag_graph import RAGGraph
from back import status_store

app = FastAPI()

# فقط یک‌بار، موقع بالا اومدن این پروسه ساخته می‌شه
rag = RAGGraph()


class AskRequest(BaseModel):
    query: str
    session_id: str
    top_k: Optional[int] = None
    max_retries: Optional[int] = None
    user_access_level: Optional[int] = None


# @app.post("/ask")
# def ask(req: AskRequest):
#     try:
#         result = rag.run(
#             query=req.query,
#             session_id=req.session_id,
#             top_k=req.top_k,
#             max_retries=req.max_retries,
#             user_access_level=req.user_access_level,
#             on_step=lambda node_name: status_store.set_step(req.session_id, node_name),
#         )
#         status_store.clear(req.session_id)
#         return result
#     except Exception as e:
#         status_store.set_error(req.session_id, str(e))
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
def ask(req: AskRequest):
    try:
        result = rag.run(
            query=req.query,
            session_id=req.session_id,
            top_k=req.top_k,
            max_retries=req.max_retries,
            user_access_level=req.user_access_level,
            on_step=lambda node_name: status_store.set_step(
                req.session_id, node_name
            ),
        )

        status_store.clear(req.session_id)
        return result

    except Exception as e:
        import traceback
        traceback.print_exc()

        status_store.set_error(req.session_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{session_id}")
def get_status(session_id: str):
    entry = status_store.get_status(session_id)
    return entry or {}