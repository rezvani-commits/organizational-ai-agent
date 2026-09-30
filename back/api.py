from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from back.rag_graph import RAGGraph
from back import status_store
from back.config import Config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag = RAGGraph()


class AskRequest(BaseModel):
    query: str
    session_id: str
    top_k: Optional[int] = None
    max_retries: Optional[int] = None
    user_access_level: Optional[int] = None


class SourceItem(BaseModel):
    chunk_id: Optional[str] = None
    name: str
    page: Optional[str] = None
    content: str
    score: Optional[float] = None
    document_id: Optional[str] = None


class ScoreItem(BaseModel):
    relevance: Optional[float] = None
    completeness: Optional[float] = None
    faithfulness: Optional[float] = None
    overall: Optional[float] = None


class AskResponse(BaseModel):
    answer: str
    session_id: str
    intent: Optional[str] = None
    sources: List[SourceItem] = []
    scores: ScoreItem = ScoreItem()
    suggestions: List[str] = []
    warning: Optional[str] = None
    is_satisfied: bool = True
    is_not_found: bool = False
    processing_time: float = 0.0
    was_rewritten: bool = False
    standalone_query: str = ""


def _map_sources(retrieved_docs: Optional[List[Dict]]) -> List[Dict]:
    sources = []
    for doc in (retrieved_docs or []):
        meta = doc.get("metadata", {}) or {}
        sources.append({
            "chunk_id": doc.get("chunk_id"),
            "name": meta.get("document_name") or "بدون عنوان",
            "page": meta.get("locator") or meta.get("section"),
            "content": doc.get("content", ""),
            "score": doc.get("fused_score"),
            "document_id": meta.get("document_id"),
        })
    return sources


def _map_scores(validation_result: Optional[Dict]) -> Dict:
    vr = validation_result or {}

    def _score_of(key: str):
        val = vr.get(key)
        return val.get("score") if isinstance(val, dict) else None

    return {
        "relevance": _score_of("relevance"),
        "completeness": _score_of("completeness"),
        "faithfulness": _score_of("faithfulness"),
        "overall": vr.get("overall_score"),
    }


def _to_ask_response(result: Dict[str, Any]) -> AskResponse:
    validation_result = result.get("validation_result") or {}
    answer = result.get("answer", "")

    is_not_found = (
        bool(validation_result.get("is_not_found", False))
        or answer.strip() == Config.NOT_FOUND_PHRASE.strip()
    )

    sources = [] if is_not_found else _map_sources(result.get("retrieved_docs"))

    return AskResponse(
        answer=answer,
        session_id=result.get("session_id", ""),
        intent=result.get("intent"),
        sources=sources,
        scores=_map_scores(validation_result),
        suggestions=result.get("suggested_questions", []) or [],
        warning=result.get("warning"),
        is_satisfied=result.get("is_satisfied", True),
        is_not_found=is_not_found,
        processing_time=result.get("processing_time", 0.0),
        was_rewritten=result.get("was_rewritten", False),
        standalone_query=result.get("standalone_query", ""),
    )


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    try:
        result = rag.run(
            query=req.query,
            session_id=req.session_id,
            top_k=req.top_k,
            max_retries=req.max_retries,
            user_access_level=req.user_access_level,
            on_step=lambda node_name: status_store.set_step(req.session_id, node_name),
        )
        status_store.clear(req.session_id)
        return _to_ask_response(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        status_store.set_error(req.session_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{session_id}")
def get_status(session_id: str):
    entry = status_store.get_status(session_id)
    return entry or {}



# =====================================================================
# Auth / User Management
# =====================================================================
import bcrypt
from auth.users import (
    get_users,
    get_user_by_username,
    create_user,
    update_user,
    set_user_active,
    change_password as db_change_password,
)


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, AttributeError):
        return False


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    username: str
    name: str
    department: str
    role: str
    level: int
    active: bool


class LoginResponse(BaseModel):
    success: bool
    message: str = ""
    user: Optional[UserOut] = None


class CreateUserRequest(BaseModel):
    username: str
    name: str
    department: str
    role: str
    level: int
    password: str


class UpdateUserRequest(BaseModel):
    name: str
    department: str
    role: str
    level: int


class SetActiveRequest(BaseModel):
    active: bool


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


def _strip_hash(user: Dict) -> Dict:
    return {k: v for k, v in user.items() if k != "password_hash"}


@app.post("/login", response_model=LoginResponse)
def login_endpoint(req: LoginRequest):
    username = (req.username or "").strip()
    user = get_user_by_username(username)

    if not user or not user.get("active", True) or not _verify_password(req.password, user["password_hash"]):
        return LoginResponse(success=False, message="نام کاربری یا رمز عبور اشتباه است.")

    return LoginResponse(success=True, user=UserOut(**_strip_hash(user)))


@app.get("/users", response_model=List[UserOut])
def list_users_endpoint():
    return [UserOut(**_strip_hash(u)) for u in get_users()]


@app.post("/users")
def create_user_endpoint(req: CreateUserRequest):
    if req.level not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="سطح دسترسی نامعتبر است.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="رمز عبور باید حداقل ۶ کاراکتر باشد.")

    hashed = _hash_password(req.password)
    ok, msg = create_user(req.username, req.name, req.department, req.role, req.level, hashed)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


@app.put("/users/{username}")
def update_user_endpoint(username: str, req: UpdateUserRequest):
    if req.level not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="سطح دسترسی نامعتبر است.")
    ok, msg = update_user(username, req.name, req.department, req.role, req.level)
    if not ok:
        raise HTTPException(status_code=404, detail=msg)
    return {"success": True, "message": msg}


@app.patch("/users/{username}/active")
def set_active_endpoint(username: str, req: SetActiveRequest):
    ok, msg = set_user_active(username, req.active)
    if not ok:
        raise HTTPException(status_code=404, detail=msg)
    return {"success": True, "message": msg}


@app.post("/users/{username}/change-password")
def change_password_endpoint(username: str, req: ChangePasswordRequest):
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد.")
    if not user.get("active", True):
        raise HTTPException(status_code=400, detail="حساب کاربری غیرفعال است.")
    if not _verify_password(req.old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="رمز عبور فعلی اشتباه است.")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="رمز عبور جدید باید حداقل ۶ کاراکتر باشد.")

    new_hash = _hash_password(req.new_password)
    ok, msg = db_change_password(username, new_hash)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}