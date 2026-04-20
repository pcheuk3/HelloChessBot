import json
import os
import re
import tempfile
import logging
import threading
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import chess
import chess.engine
import replicate
from replicate.exceptions import ReplicateError
from dotenv import load_dotenv
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field, field_validator
from fastapi.middleware.cors import CORSMiddleware
# =========================
# Logging
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("hellochessbot_api")

# =========================
# Environment setup
# =========================
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _load_readme_guide() -> str:
    readme_path = BASE_DIR / "README.md"
    try:
        content = readme_path.read_text(encoding="utf-8").strip()
        if not content:
            logger.warning("README.md is empty")
        return content
    except Exception:
        logger.exception("Failed to load README.md")
        return ""


README_GUIDE = _load_readme_guide()
README_FALLBACK_GUIDE = (
    "README.md could not be loaded. Provide a brief, generic help reply and "
    "ask the user what they want to do."
)

os.environ["HF_HOME"] = str(BASE_DIR / "hf_cache")
os.environ["HUGGINGFACE_HUB_CACHE"] = str(BASE_DIR / "hf_cache")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_SAFE_MOVE"] = "1"

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
APP_API_KEY = os.getenv("APP_API_KEY")
STOCKFISH_PATH = os.getenv("STOCKFISH_PATH")

if not REPLICATE_API_TOKEN:
    raise RuntimeError("REPLICATE_API_TOKEN not set in .env")

if not STOCKFISH_PATH:
    raise RuntimeError("STOCKFISH_PATH not set in .env")

replicate_client = replicate.Client(api_token=REPLICATE_API_TOKEN)

_STOCKFISH_ENGINE_LOCK = threading.Lock()
_STOCKFISH_ENGINE: Optional[chess.engine.SimpleEngine] = None
_SESSION_CLEANUP_STOP_EVENT = threading.Event()
_SESSION_CLEANUP_THREAD: Optional[threading.Thread] = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _SESSION_CLEANUP_THREAD

    if _SESSION_CLEANUP_THREAD is None or not _SESSION_CLEANUP_THREAD.is_alive():
        _SESSION_CLEANUP_STOP_EVENT.clear()
        _SESSION_CLEANUP_THREAD = threading.Thread(target=session_cleanup_worker, daemon=True)
        _SESSION_CLEANUP_THREAD.start()

    # Eager-init STT on startup so first /stt request has no cold-start delay.
    # If the model is not cached yet, faster-whisper will download it automatically.
    if ensure_stt_model_loaded() is None:
        logger.warning("STT model is unavailable after startup initialization.")

    try:
        yield
    finally:
        _SESSION_CLEANUP_STOP_EVENT.set()
        _close_stockfish_engine()


app = FastAPI(title="HelloChessBot API", lifespan=lifespan)

cors_origins_env = os.getenv("CORS_ALLOW_ORIGINS", "*")
allow_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
if not allow_origins:
    allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# Session Management
# =========================
# Storage structure: { session_id: {"history": deque, "last_active": timestamp} }
SESSIONS: Dict[str, Dict[str, Any]] = {}
SESSIONS_LOCK = threading.Lock()
SESSION_TIMEOUT = 7200  # 2 hours of inactivity auto-cleanup
MAX_HISTORY_LEN = 10    # 5 turns of conversation (5 user + 5 assistant)

def get_or_create_session(session_id: str):
    now = time.time()
    with SESSIONS_LOCK:
        if session_id not in SESSIONS:
            SESSIONS[session_id] = {
                "history": deque(maxlen=MAX_HISTORY_LEN),
                "last_active": now,
                "pending_move": None,
                "preferred_language": None,
            }
        else:
            SESSIONS[session_id]["last_active"] = now

            if "pending_move" not in SESSIONS[session_id]:
                SESSIONS[session_id]["pending_move"] = None
            if "history" not in SESSIONS[session_id]:
                SESSIONS[session_id]["history"] = deque(maxlen=MAX_HISTORY_LEN)
            if "preferred_language" not in SESSIONS[session_id]:
                SESSIONS[session_id]["preferred_language"] = None

        return SESSIONS[session_id]
def session_cleanup_worker():
    """Background thread: clean up expired user data every 10 minutes"""
    while not _SESSION_CLEANUP_STOP_EVENT.is_set():
        if _SESSION_CLEANUP_STOP_EVENT.wait(timeout=600):
            break

        now = time.time()
        with SESSIONS_LOCK:
            expired_ids = [
                sid for sid, data in SESSIONS.items()
                if now - data["last_active"] > SESSION_TIMEOUT
            ]
            for sid in expired_ids:
                del SESSIONS[sid]
                logger.info(f"Cleaned up expired session: {sid}")

# =========================
# STT model (faster-whisper)
# =========================
STT_MODEL = None
_STT_MODEL_LOCK = threading.Lock()
_STT_MODEL_INIT_ATTEMPTED = False


def ensure_stt_model_loaded() -> Optional[Any]:
    """Load Whisper model (auto-download on first run if cache is missing)."""
    global STT_MODEL, _STT_MODEL_INIT_ATTEMPTED

    if STT_MODEL is not None:
        return STT_MODEL

    with _STT_MODEL_LOCK:
        if STT_MODEL is not None:
            return STT_MODEL

        if _STT_MODEL_INIT_ATTEMPTED:
            return None

        _STT_MODEL_INIT_ATTEMPTED = True

        try:
            from faster_whisper import WhisperModel
        except Exception:
            logger.exception("Failed to import faster_whisper")
            return None

        logger.info("Loading STT model: large-v3 (auto-download if not cached) ...")
        try:
            STT_MODEL = WhisperModel(
                "large-v3",
                device="cuda",
                compute_type="float16",
                download_root=os.environ["HF_HOME"],
                local_files_only=False,
            )
            logger.info("Loaded STT model on GPU")
        except Exception:
            try:
                STT_MODEL = WhisperModel(
                    "large-v3",
                    device="cpu",
                    compute_type="int8",
                    download_root=os.environ["HF_HOME"],
                    local_files_only=False,
                )
                logger.info("Loaded STT model on CPU")
            except Exception:
                logger.exception("Failed to load STT model")
                STT_MODEL = None

        return STT_MODEL

# =========================
# Constants
# =========================
ANALYSIS_PROMPT_PREFIXES = ("code 8888",)
ANALYSIS_PREFIX_STRIP_RE = re.compile(
    r"^\s*code[\s:\-_/]*8888\b[\s:,\-]*",
    re.IGNORECASE,
)

INTENT_LIST = [
    "start_computer_game",
    "start_online_game",
    "start_puzzle",
    "resign",
    "open_settings",
    "login",
    "logout",
    "return_home",
    "undo_last_move",
    "move_piece",
    "ask_situation",
    "ask_help",
    "unknown",
]

ACTION_INTENTS = {
    "start_computer_game",
    "start_online_game",
    "start_puzzle",
    "resign",
    "open_settings",
    "login",
    "logout",
    "return_home",
    "undo_last_move",
    "ask_help",
}

MOVE_VERBS = {
    "move", "play", "go", "take", "takes", "capture", "captures",
    "castle", "push", "put", "drop"
}

PIECE_NAME_TO_TYPE = {
    "king": chess.KING,
    "queen": chess.QUEEN,
    "rook": chess.ROOK,
    "bishop": chess.BISHOP,
    "knight": chess.KNIGHT,
    "horse": chess.KNIGHT,
    "pawn": chess.PAWN,
    # common abbreviations
    "k": chess.KING,
    "q": chess.QUEEN,
    "r": chess.ROOK,
    "b": chess.BISHOP,
    "n": chess.KNIGHT,
    "p": chess.PAWN,
}

PROMOTION_NAME_TO_TYPE = {
    "queen": chess.QUEEN,
    "rook": chess.ROOK,
    "bishop": chess.BISHOP,
    "knight": chess.KNIGHT,
    "q": chess.QUEEN,
    "r": chess.ROOK,
    "b": chess.BISHOP,
    "n": chess.KNIGHT,
}

# =========================
# Request / Response Models
# =========================
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=3000)
    session_id: str = Field(default="default", max_length=128)
    fen: Optional[str] = Field(default=None, max_length=200)
    level: str = Field(default="beginner")
    depth: int = Field(default=14, ge=8, le=24)
    multipv: int = Field(default=3, ge=1, le=5)
    user_color: Optional[str] = Field(default=None)
    in_game: bool = Field(default=False)

    @field_validator("fen")
    @classmethod
    def validate_fen(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not str(v).strip():
            return None

        fen = str(v).strip()
        try:
            board = chess.Board(fen)
        except Exception as e:
            raise ValueError(f"Invalid FEN: {e}")

        if board.king(chess.WHITE) is None or board.king(chess.BLACK) is None:
            raise ValueError("Invalid FEN: both kings must be present")

        if not board.is_valid():
            raise ValueError("Invalid FEN: position is not legally valid")

        return fen

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        allowed = {"beginner", "intermediate", "advanced"}
        if v not in allowed:
            raise ValueError(f"level must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("user_color")
    @classmethod
    def validate_user_color(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.lower().strip()
        if v not in {"white", "black"}:
            raise ValueError("user_color must be 'white' or 'black'")
        return v


class ChatResponse(BaseModel):
    ok: bool
    mode: str
    reply: str
    intent: str
    action: Optional[str] = None

    move_uci: Optional[str] = None
    move_san: Optional[str] = None

    candidate_move_raw: Optional[str] = None
    candidate_move_uci: Optional[str] = None
    candidate_move_san: Optional[str] = None

    reasoning: Optional[str] = None

    board_facts: Optional[Dict[str, Any]] = None
    engine_analysis: Optional[Dict[str, Any]] = None


# =========================
# Utility helpers
# =========================
def _normalize_analysis_trigger_text(message: str) -> str:
    text = (message or "").strip().lower()
    # tolerate punctuation/spacing variants, e.g. "code:8888", "code 8888", "code-8888"
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_analysis_prompt(message: str) -> bool:
    text = _normalize_analysis_trigger_text(message)
    return any(text.startswith(prefix) for prefix in ANALYSIS_PROMPT_PREFIXES)


def strip_analysis_prefix(message: str) -> str:
    text = (message or "").strip()
    if not text:
        return ""
    if not is_analysis_prompt(text):
        return text
    return ANALYSIS_PREFIX_STRIP_RE.sub("", text, count=1).strip()


def parse_color(color: Optional[str]) -> Optional[bool]:
    if color == "white":
        return chess.WHITE
    if color == "black":
        return chess.BLACK
    return None


def map_intent_to_action(intent: str) -> Optional[str]:
    if intent in ACTION_INTENTS:
        return intent
    if intent == "ask_situation":
        return "ask_situation"
    return None


def safe_json_loads(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {
            "reply": "",
            "intent": "unknown",
            "reasoning": "Model output was empty.",
        }

    try:
        return json.loads(text)
    except Exception:
        pass

    # Try fenced JSON block first
    fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
    if fence_match:
        candidate = fence_match.group(1).strip()
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Fallback: scan balanced JSON objects and parse the first valid one
    decoder = json.JSONDecoder()
    for idx, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _end = decoder.raw_decode(text[idx:])
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue

    return {
        "reply": text,
        "intent": "unknown",
        "reasoning": "Model output was not valid strict JSON.",
    }


def first_non_empty(*values: Optional[str]) -> Optional[str]:
    for v in values:
        if v is not None and str(v).strip():
            return str(v).strip()
    return None


def _normalized_session_id(session_id: Optional[str]) -> str:
    sid = (session_id or "default").strip()
    return sid[:128] or "default"


def _format_history_for_prompt(history: List[Dict[str, str]], max_items: int = 12) -> str:
    if not history:
        return "(no previous conversation)"

    recent = history[-max_items:]
    lines: List[str] = []
    for item in recent:
        role = str(item.get("role", "user")).strip().lower()
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        if role not in {"user", "assistant"}:
            role = "user"
        lines.append(f"{role}: {content}")

    return "\n".join(lines) if lines else "(no previous conversation)"


def infer_preferred_language_from_history(history: List[Dict[str, str]]) -> Optional[str]:
    """Infer language from latest meaningful history content.

    Priority:
    1) latest non-analysis user message
    2) latest assistant message (fallback when user text is too short/empty)
    """
    # 1) user messages first
    for item in reversed(history):
        role = str(item.get("role", "")).strip().lower()
        if role != "user":
            continue

        content = str(item.get("content", "")).strip()
        if not content:
            continue

        content_wo_prefix = strip_analysis_prefix(content)
        lang = detect_text_language(content_wo_prefix)
        if lang != "unknown":
            return lang

    # 2) assistant fallback
    for item in reversed(history):
        role = str(item.get("role", "")).strip().lower()
        if role != "assistant":
            continue

        content = str(item.get("content", "")).strip()
        if not content:
            continue

        lang = detect_text_language(content)
        if lang != "unknown":
            return lang

    return None


SUPPORTED_RESPONSE_LANGUAGES = {"en", "zh-cn", "zh-tw", "yue"}
SUPPORTED_STT_INPUT_LANGUAGES = {"en", "zh-cn", "yue"}

def _resolve_zh_variant_from_text(text: str) -> str:
    t = (text or "").lower()
    yue_patterns = [
        r"佢",
        r"你哋|我哋",
        r"咩|乜",
        r"點|點樣",
        r"冇",
        r"唔",
        r"喺|係咪|而家|咁|嘅|啲|嚟|咗",
        r"\b(keoi|nei|gam|dim|la|lor|lo|ge)\b",
    ]

    # Any clear Cantonese marker is enough to classify as Cantonese.
    if any(re.search(pattern, t) for pattern in yue_patterns):
        return "yue"

    simplified_markers = len(re.findall(r"[这说为后会个国点现应边吗么们]", text))
    traditional_markers = len(re.findall(r"[這說為後會個國點現應邊嗎麼們]", text))

    # Mandarin script hints
    if simplified_markers > traditional_markers:
        return "zh-cn"

    if traditional_markers > simplified_markers:
        return "zh-tw"

    # If only weak/neutral Chinese evidence, keep Mandarin fallback.
    return "zh-cn"


def normalize_language_code(raw_lang: Optional[str], text_hint: Optional[str] = None) -> str:
    lang = (raw_lang or "").strip().lower().replace("_", "-")
    text = (text_hint or "").strip()

    if not lang:
        return "unknown"

    if lang in {"en", "en-us", "en-gb"}:
        return "en"

    if lang in {"yue", "zh-yue", "yue-hk"}:
        return "yue"

    if lang.startswith("zh"):
        return _resolve_zh_variant_from_text(text)

    if lang.startswith("ja"):
        return "ja"

    if lang.startswith("ko"):
        return "ko"

    return lang


def detect_text_language(message: str) -> str:
    text = (message or "").strip()
    if not text:
        return "unknown"

    # Chinese script detection first
    if re.search(r"[\u4e00-\u9fff]", text):
        return normalize_language_code("zh", text_hint=text)

    # Latin-script heuristic: do NOT treat every Latin sentence as English.
    # This avoids false positives such as Malay/Indonesian being classified as "en".
    if re.search(r"[A-Za-z]", text):
        tokens = re.findall(r"[a-z]+", text.lower())
        if not tokens:
            return "unknown"

        english_clues = {
            "the", "is", "are", "am", "a", "an", "to", "for", "of", "and", "or",
            "what", "why", "how", "where", "when", "who", "which",
            "please", "help", "move", "best", "position", "now", "chess", "board",
            "pawn", "knight", "bishop", "rook", "queen", "king", "castle",
        }
        english_hits = sum(1 for t in tokens if t in english_clues)

        # Accept English when there is clear signal.
        if english_hits >= 2:
            return "en"

        # Very short commands with one strong chess/English keyword are also allowed.
        if len(tokens) <= 3 and english_hits >= 1:
            return "en"

        return "unknown"

    return "unknown"


def choose_response_language(
    *,
    stt_language: Optional[str],
    message: str,
    session_preferred_language: Optional[str],
) -> str:
    stt_lang = normalize_language_code(stt_language, text_hint=message)
    if stt_lang != "unknown":
        return stt_lang

    text_lang = detect_text_language(message)
    if text_lang != "unknown":
        return text_lang

    pref = normalize_language_code(session_preferred_language, text_hint=message)
    if pref != "unknown":
        return pref

    return "en"


def normalize_stt_input_language(lang: str) -> str:
    # For STT gating, treat Traditional Mandarin as Mandarin.
    if lang == "zh-tw":
        return "zh-cn"
    return lang


def preprocess_user_message(message: str) -> str:
    text = (message or "").replace("\u2019", "'")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def resolve_intent_reply(
    intent: str,
    llm_reply: Optional[str],
    *,
    move_piece_needs_detail: bool = False,
    ask_situation_needs_fen: bool = False,
) -> str:
    base_reply = first_non_empty(llm_reply) or "Sorry, I could not understand that."

    fixed_replies = {
        "login": "Logging in now...",
        "logout": "Logging out now...",
        "return_home": "Returning to the home page now...",
        "undo_last_move": "Undoing the last move now...",
    }

    if intent in fixed_replies:
        return first_non_empty(llm_reply, fixed_replies[intent]) or fixed_replies[intent]

    if intent == "ask_situation" and ask_situation_needs_fen:
        fallback = "Please send the current FEN so I can describe the position."
        return first_non_empty(llm_reply, fallback) or fallback

    if intent == "move_piece" and move_piece_needs_detail:
        return (
            "I understood you want to move a piece, but I need more detail. "
            "Please tell me the destination square (for example: 'pawn to e4')."
        )

    return base_reply


# =========================
# Chess speech normalization
# =========================
def normalize_chess_speech_text(text: str) -> str:
    text = (text or "").lower().strip()
    text = text.replace("’", "'").replace("‘", "'")

    # tolerate spoken/chat punctuation that often appears in STT or typing,
    # e.g. "e4.", "knight f3?", "move to d4，"
    # Keep '-' because castling patterns (o-o / 0-0) rely on it before normalization.
    text = re.sub(r"[.,!?;:，。！？；：、()\[\]{}\"“”]+", " ", text)


    text = re.sub(r"\s+", " ", text)

    replacements = [
        # piece names
        (r"\bknife\b", "knight"),
        (r"\bknifes\b", "knights"),
        (r"\bnight\b", "knight"),
        (r"\bnights\b", "knights"),
        (r"\bnite\b", "knight"),
        (r"\bhorse\b", "knight"),
        (r"\bhorses\b", "knights"),

        (r"\bdishes\b", "bishop"),
        (r"\bdish\b", "bishop"),
        (r"\bbisop\b", "bishop"),
        (r"\bbishops\b", "bishop"),

        (r"\blook\b", "rook"),
        (r"\brooks\b", "rook"),
        (r"\bbook\b", "rook"),
        (r"\bwork\b", "rook"),

  

        (r"\bquinn\b", "queen"),
   

        (r"\bporn\b", "pawn"),
        (r"\bpond\b", "pawn"),
        (r"\bpawns\b", "pawn"),
        (r"\bproblem\b", "pawn"),
        (r"\bprompt\b", "pawn"),

        # castling
        (r"\bcast all\b", "castle"),
        (r"\bking side\b", "kingside"),
        (r"\bkings side\b", "kingside"),
        (r"\bqueen side\b", "queenside"),

        # connectors / misc
        (r"\bonto\b", "to"),
        (r"\bgoing to\b", "to"),
        (r"\bgo to\b", "to"),
        (r"\bmove it to\b", "to"),
        (r"\bmove to\b", "to"),
    ]

    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)

    square_phrase_map = {
        "before": "b4",
        "be four": "b4",
        "bee four": "b4",
        "b four": "b4",
        "see four": "c4",
        "sea four": "c4",
        "c four": "c4",
        "dee four": "d4",
        "d four": "d4",
        "e four": "e4",
        "e for": "e4",
        "f three": "f3",
        "f 3": "f3",
        "g one": "g1",
        "g 1": "g1",
        "g three": "g3",
        "gee three": "g3",
        "g 3": "g3",
        "c six": "c6",
        "c 6": "c6",
        "e two": "e2",
        "e to": "e2",
        "d two": "d2",
        "d to": "d2",
        "f two": "f2",
        "a three": "a3",
        "h three": "h3",
        "h eight": "h8",
        "h ate": "h8",
        "h 8": "h8",
    }

    for k, v in square_phrase_map.items():
        text = re.sub(rf"\b{k}\b", v, text)

    file_words = {
        "a": "a", "ay": "a", "eh": "a",
        "b": "b", "bee": "b", "be": "b",
        "c": "c", "sea": "c", "see": "c",
        "d": "d", "dee": "d",
        "e": "e",
        "f": "f", "ef": "f",
        "g": "g", "gee": "g",
        "h": "h", "aitch": "h",
    }
    rank_words = {
        "one": "1", "won": "1",
        "two": "2",
        "three": "3",
        "four": "4", "for": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8", "ate": "8",
    }

    tokens = text.split()
    merged = []
    i = 0
    while i < len(tokens):
        if i + 1 < len(tokens):
            f = file_words.get(tokens[i])
            r = rank_words.get(tokens[i + 1])
            if f and r:
                merged.append(f + r)
                i += 2
                continue
        merged.append(tokens[i])
        i += 1

    text = " ".join(merged)

    # normalize SAN-style O-O / 0-0 spellings
    text = text.replace("o - o - o", "ooo")
    text = text.replace("o-o-o", "ooo")
    text = text.replace("0-0-0", "ooo")
    text = text.replace("o - o", "oo")
    text = text.replace("o-o", "oo")
    text = text.replace("0-0", "oo")

    # tidy
    text = re.sub(r"\s+", " ", text).strip()
    logger.info("Normalized user text: %s", text)
    return text


# =========================
# Board facts
# =========================
def get_piece_map(board: chess.Board, color: bool) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {
        "king": [],
        "queen": [],
        "rook": [],
        "bishop": [],
        "knight": [],
        "pawn": [],
    }

    for sq, piece in board.piece_map().items():
        if piece.color == color:
            name = chess.piece_name(piece.piece_type)
            result[name].append(chess.square_name(sq))

    for k in result:
        result[k].sort()

    return result


def attacked_pieces(board: chess.Board, color: bool) -> List[Dict[str, str]]:
    items = []
    for sq, piece in board.piece_map().items():
        if piece.color == color and board.is_attacked_by(not color, sq):
            items.append({
                "piece": chess.piece_name(piece.piece_type),
                "square": chess.square_name(sq),
            })
    return items


def pinned_pieces(board: chess.Board, color: bool) -> List[Dict[str, str]]:
    items = []
    for sq, piece in board.piece_map().items():
        if piece.color == color and board.is_pinned(color, sq):
            items.append({
                "piece": chess.piece_name(piece.piece_type),
                "square": chess.square_name(sq),
            })
    return items


def hanging_pieces(board: chess.Board, color: bool) -> List[Dict[str, str]]:
    items = []
    for sq, piece in board.piece_map().items():
        if piece.color != color:
            continue

        attacked = board.is_attacked_by(not color, sq)
        defended = board.is_attacked_by(color, sq)
        if attacked and not defended:
            items.append({
                "piece": chess.piece_name(piece.piece_type),
                "square": chess.square_name(sq),
            })
    return items


def material_count(board: chess.Board, color: bool) -> int:
    values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0,
    }
    total = 0
    for _, piece in board.piece_map().items():
        if piece.color == color:
            total += values.get(piece.piece_type, 0)
    return total


def legal_moves_preview(board: chess.Board, limit: int = 20) -> List[str]:
    out = []
    for i, mv in enumerate(board.legal_moves):
        if i >= limit:
            break
        try:
            out.append(board.san(mv))
        except Exception:
            out.append(mv.uci())
    return out


def compute_board_facts(board: chess.Board, user_color: Optional[str]) -> Dict[str, Any]:
    facts: Dict[str, Any] = {
        "fen": board.fen(),
        "side_to_move": "white" if board.turn == chess.WHITE else "black",
        "fullmove_number": board.fullmove_number,
        "halfmove_clock": board.halfmove_clock,
        "is_check": board.is_check(),
        "is_checkmate": board.is_checkmate(),
        "is_stalemate": board.is_stalemate(),
        "is_insufficient_material": board.is_insufficient_material(),
        "can_claim_draw": board.can_claim_draw(),
        "legal_moves_preview": legal_moves_preview(board, 20),
        "ep_square": chess.square_name(board.ep_square) if board.ep_square is not None else None,
        "castling_rights": {
            "white_kingside": board.has_kingside_castling_rights(chess.WHITE),
            "white_queenside": board.has_queenside_castling_rights(chess.WHITE),
            "black_kingside": board.has_kingside_castling_rights(chess.BLACK),
            "black_queenside": board.has_queenside_castling_rights(chess.BLACK),
        },
    }

    user_side = parse_color(user_color)
    if user_side is not None:
        opp_side = not user_side
        facts["user_color"] = user_color
        facts["user_pieces"] = get_piece_map(board, user_side)
        facts["opponent_pieces"] = get_piece_map(board, opp_side)
        facts["user_attacked_pieces"] = attacked_pieces(board, user_side)
        facts["opponent_attacked_pieces"] = attacked_pieces(board, opp_side)
        facts["user_pinned_pieces"] = pinned_pieces(board, user_side)
        facts["opponent_pinned_pieces"] = pinned_pieces(board, opp_side)
        facts["user_hanging_pieces"] = hanging_pieces(board, user_side)
        facts["opponent_hanging_pieces"] = hanging_pieces(board, opp_side)
        facts["material_user"] = material_count(board, user_side)
        facts["material_opponent"] = material_count(board, opp_side)
        facts["material_diff"] = facts["material_user"] - facts["material_opponent"]

    return facts


# =========================
# Stockfish analysis
# =========================
def _get_stockfish_engine() -> chess.engine.SimpleEngine:
    global _STOCKFISH_ENGINE

    if _STOCKFISH_ENGINE is None:
        logger.info("Starting persistent Stockfish engine process")
        _STOCKFISH_ENGINE = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    return _STOCKFISH_ENGINE


def _close_stockfish_engine() -> None:
    global _STOCKFISH_ENGINE

    with _STOCKFISH_ENGINE_LOCK:
        if _STOCKFISH_ENGINE is not None:
            try:
                _STOCKFISH_ENGINE.quit()
            except chess.engine.EngineTerminatedError:
                logger.warning("Stockfish engine already terminated while closing")
            except Exception:
                logger.exception("Failed to quit Stockfish engine cleanly")
            finally:
                _STOCKFISH_ENGINE = None


def analyze_with_stockfish(board: chess.Board, depth: int = 14, multipv: int = 3) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "turn": "white" if board.turn == chess.WHITE else "black",
        "fullmove_number": board.fullmove_number,
        "is_check": board.is_check(),
        "is_checkmate": board.is_checkmate(),
        "is_stalemate": board.is_stalemate(),
        "best_move_uci": None,
        "best_move_san": None,
        "evaluation_cp": None,
        "mate": None,
        "top_lines": [],
    }

    if board.is_game_over():
        return result

    safe_depth = max(8, min(int(depth), 24))
    safe_multipv = max(1, min(int(multipv), 5))

    def _run_analysis_once() -> Any:
        with _STOCKFISH_ENGINE_LOCK:
            engine = _get_stockfish_engine()
            return engine.analyse(
                board,
                chess.engine.Limit(depth=safe_depth),
                multipv=safe_multipv,
            )

    try:
        info_list = _run_analysis_once()
    except chess.engine.EngineTerminatedError:
        logger.warning("Stockfish engine died during analyse(); restarting engine and retrying once")
        _close_stockfish_engine()
        try:
            info_list = _run_analysis_once()
        except Exception as e:
            logger.exception("Stockfish analysis failed after engine restart")
            result["error"] = str(e)
            _close_stockfish_engine()
            return result
    except Exception as e:
        logger.exception("Stockfish analysis failed")
        result["error"] = str(e)
        _close_stockfish_engine()
        return result

    if isinstance(info_list, dict):
        info_list = [info_list]

    for idx, info in enumerate(info_list, start=1):
        pv = info.get("pv", [])
        score = info.get("score")

        move_uci = pv[0].uci() if pv else None
        move_san = None
        if pv:
            try:
                move_san = board.san(pv[0])
            except Exception:
                move_san = pv[0].uci()

        cp = None
        mate = None
        if score is not None:
            pov = score.pov(board.turn)
            cp = pov.score(mate_score=100000)
            mate = pov.mate()

        result["top_lines"].append({
            "rank": idx,
            "move_uci": move_uci,
            "move_san": move_san,
            "evaluation_cp": cp,
            "mate": mate,
            "pv_uci": [m.uci() for m in pv[:10]],
        })

    if result["top_lines"]:
        best = result["top_lines"][0]
        result["best_move_uci"] = best["move_uci"]
        result["best_move_san"] = best["move_san"]
        result["evaluation_cp"] = best["evaluation_cp"]
        result["mate"] = best["mate"]

    return result


# =========================
# Move parsing / validation
# =========================
def normalize_move_text(text: str) -> str:
    text = normalize_chess_speech_text(text)
    text = text.replace("-", " ")
    text = re.sub(r"\bon\b", " ", text)
    text = re.sub(r"\bat\b", " ", text)
    text = re.sub(r"\bx\b", " capture ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def try_parse_san_or_uci(raw: str, board: chess.Board) -> Optional[chess.Move]:
    if not raw:
        return None

    raw = raw.strip()
    raw_lower = raw.lower()

    # support space-separated UCI like "b2 b4" / "e7 e8 q"
    compact_uci = raw_lower.replace(" ", "")

    if re.fullmatch(r"[a-h][1-8][a-h][1-8][qrbn]?", compact_uci):
        try:
            mv = chess.Move.from_uci(compact_uci)
            if mv in board.legal_moves:
                return mv
        except Exception:
            pass

    san_candidates = [raw, raw.replace(" ", "")]

    # tolerate lowercase SAN from STT/normalization: nbd2 -> Nbd2, qxe7+ -> Qxe7+
    compact_raw = raw.replace(" ", "")
    if re.fullmatch(r"[nbrqk][a-h]?[1-8]?x?[a-h][1-8](=[nbrq])?[+#]?", compact_raw.lower()):
        san_candidates.append(compact_raw[0].upper() + compact_raw[1:])

    for san_text in san_candidates:
        try:
            mv = board.parse_san(san_text)
            if mv in board.legal_moves:
                return mv
        except Exception:
            continue

    return None


def try_extract_move_from_square_path(raw: str, board: chess.Board) -> Optional[chess.Move]:
    """Parse moves from texts like '從c1走到d2' or 'c1 to d2' without extra LLM calls."""
    text = (raw or "").lower()
    squares = re.findall(r"\b([a-h][1-8])\b", text)
    if len(squares) < 2:
        return None

    # Prefer the last path in sentence (e.g. ... c1 ... d2)
    from_sq, to_sq = squares[-2], squares[-1]

    promotion = ""
    promo_match = re.search(r"\b(?:promote|promotion|=)\s*(q|r|b|n|queen|rook|bishop|knight)\b", text)
    if promo_match:
        promo_token = promo_match.group(1)
        promo_map = {
            "queen": "q", "rook": "r", "bishop": "b", "knight": "n",
            "q": "q", "r": "r", "b": "b", "n": "n",
        }
        promotion = promo_map.get(promo_token, "")

    uci = f"{from_sq}{to_sq}{promotion}"
    try:
        mv = chess.Move.from_uci(uci)
        if mv in board.legal_moves:
            return mv
    except Exception:
        return None

    return None


def _parse_move_intent_from_text(message: str) -> Dict[str, Any]:
    text = normalize_move_text(message)

    dest_sq = None

    to_match = re.search(r"\bto\s+([a-h][1-8])\b", text)
    if to_match:
        try:
            dest_sq = chess.parse_square(to_match.group(1))
        except Exception:
            dest_sq = None
    else:
        all_squares = re.findall(r"\b([a-h][1-8])\b", text)
        if all_squares:
            try:
                dest_sq = chess.parse_square(all_squares[-1])
            except Exception:
                dest_sq = None

    piece_type = chess.PAWN
    # choose piece by earliest mention in text (not by dict order),
    # so phrases like "pawn ... become queen" still parse as a pawn move.
    earliest_idx = None
    for name, ptype in PIECE_NAME_TO_TYPE.items():
        m = re.search(rf"\b{name}\b", text)
        if not m:
            continue
        if earliest_idx is None or m.start() < earliest_idx:
            earliest_idx = m.start()
            piece_type = ptype

    promotion_type = None
    promotion_requested = bool(re.search(r"\b(promote|promotion|become|turn into|=)\b", text))
    if not promotion_requested:
        promotion_requested = bool(re.search(r"\b[a-h][1-8]\s+(queen|rook|bishop|knight|q|r|b|n)\b", text))

    if promotion_requested:
        for name, ptype in PROMOTION_NAME_TO_TYPE.items():
            if re.search(rf"\b{name}\b", text):
                promotion_type = ptype
                break

    from_file = None
    from_rank = None

    source_hint = re.search(r"\b(from|on)\s+([a-h][1-8]|[a-h]|[1-8])\b", text)
    if source_hint:
        hint = source_hint.group(2)
        if re.fullmatch(r"[a-h]", hint):
            from_file = hint
        elif re.fullmatch(r"[1-8]", hint):
            from_rank = hint
        elif re.fullmatch(r"[a-h][1-8]", hint):
            from_file = hint[0]
            from_rank = hint[1]
    else:
        # support phrases like "c7 moves to c8"
        path_hint = re.search(r"\b([a-h][1-8])\b[\w\s,]*\bto\s+([a-h][1-8])\b", text)
        if path_hint:
            from_file = path_hint.group(1)[0]
            from_rank = path_hint.group(1)[1]

    return {
        "text": text,
        "dest_sq": dest_sq,
        "piece_type": piece_type,
        "from_file": from_file,
        "from_rank": from_rank,
        "promotion_type": promotion_type,
    }


def possible_legal_moves_to_square(board: chess.Board, dest_sq: chess.Square) -> List[str]:
    out = []
    for mv in board.legal_moves:
        if mv.to_square == dest_sq:
            try:
                out.append(board.san(mv))
            except Exception:
                out.append(mv.uci())
    return out


def explain_illegal_move_from_text(message: str, board: chess.Board) -> str:
    parsed = _parse_move_intent_from_text(message)
    dest_sq = parsed["dest_sq"]
    piece_type = parsed["piece_type"]
    from_file = parsed["from_file"]
    from_rank = parsed["from_rank"]

    if dest_sq is None:
        return "I could not find a valid target square."

    piece_name = chess.piece_name(piece_type)
    player_color = board.turn

    if not list(board.pieces(piece_type, player_color)):
        return f"You don't have any {piece_name}s to move."

    dest_piece = board.piece_at(dest_sq)
    if dest_piece and dest_piece.color == player_color:
        return "That square is occupied by your own piece."

    pseudo_candidates = []
    for mv in board.generate_pseudo_legal_moves():
        if mv.to_square != dest_sq:
            continue

        piece = board.piece_at(mv.from_square)
        if not piece or piece.piece_type != piece_type:
            continue

        from_sq_name = chess.square_name(mv.from_square)
        if from_file and from_sq_name[0] != from_file:
            continue
        if from_rank and from_sq_name[1] != from_rank:
            continue

        pseudo_candidates.append(mv)

    if board.is_check() and pseudo_candidates and not any(board.is_legal(mv) for mv in pseudo_candidates):
        return "You are in check, and that move does not get you out of check."

    if pseudo_candidates:
        return "That move is not legal in this position."

    dest_name = chess.square_name(dest_sq)
    for from_sq in board.pieces(piece_type, player_color):
        from_sq_name = chess.square_name(from_sq)
        if from_file and from_sq_name[0] != from_file:
            continue
        if from_rank and from_sq_name[1] != from_rank:
            continue

        if piece_type == chess.ROOK:
            if from_sq_name[0] != dest_name[0] and from_sq_name[1] != dest_name[1]:
                return "A rook moves in straight lines (same file or rank)."
            if board.occupied & chess.BB_BETWEEN[from_sq][dest_sq]:
                return "The rook's path is blocked."

        if piece_type == chess.BISHOP:
            if abs(ord(from_sq_name[0]) - ord(dest_name[0])) != abs(int(from_sq_name[1]) - int(dest_name[1])):
                return "A bishop moves diagonally."
            if board.occupied & chess.BB_BETWEEN[from_sq][dest_sq]:
                return "The bishop's diagonal is blocked."

        if piece_type == chess.QUEEN:
            same_file = from_sq_name[0] == dest_name[0]
            same_rank = from_sq_name[1] == dest_name[1]
            diag = abs(ord(from_sq_name[0]) - ord(dest_name[0])) == abs(int(from_sq_name[1]) - int(dest_name[1]))
            if not (same_file or same_rank or diag):
                return "A queen moves in straight lines or diagonally."
            if board.occupied & chess.BB_BETWEEN[from_sq][dest_sq]:
                return "The queen's path is blocked."

        if piece_type == chess.KNIGHT:
            df = abs(ord(from_sq_name[0]) - ord(dest_name[0]))
            dr = abs(int(from_sq_name[1]) - int(dest_name[1]))
            if not ((df == 1 and dr == 2) or (df == 2 and dr == 1)):
                return "A knight moves in an L shape."

        if piece_type == chess.KING:
            df = abs(ord(from_sq_name[0]) - ord(dest_name[0]))
            dr = abs(int(from_sq_name[1]) - int(dest_name[1]))
            if max(df, dr) > 1:
                return "A king moves one square at a time (except castling)."

        if piece_type == chess.PAWN:
            direction = 1 if player_color == chess.WHITE else -1
            from_file_idx = ord(from_sq_name[0])
            to_file_idx = ord(dest_name[0])
            from_rank_idx = int(from_sq_name[1])
            to_rank_idx = int(dest_name[1])
            file_delta = to_file_idx - from_file_idx
            rank_delta = to_rank_idx - from_rank_idx

            if file_delta == 0 and rank_delta == direction:
                if board.piece_at(dest_sq) is not None:
                    return "A pawn cannot move forward into an occupied square."
                return "That pawn move is not legal."

            if file_delta == 0 and rank_delta == 2 * direction:
                start_rank = 2 if player_color == chess.WHITE else 7
                if from_rank_idx != start_rank:
                    return "A pawn can move two squares only from its starting rank."
                intermediate = chess.parse_square(f"{from_sq_name[0]}{from_rank_idx + direction}")
                if board.piece_at(intermediate) or board.piece_at(dest_sq):
                    return "A pawn cannot jump over pieces."
                return "That pawn move is not legal."

            if abs(file_delta) == 1 and rank_delta == direction:
                if board.piece_at(dest_sq) is None:
                    if board.ep_square == dest_sq:
                        return "This looks like an en passant capture, but it is not legal in the current position."
                    return "A pawn captures diagonally, but there is nothing to capture."
                return "That pawn capture is not legal."

            return "A pawn moves forward and captures diagonally."

    possible = possible_legal_moves_to_square(board, dest_sq)
    if possible:
        return f"That move is not legal. Legal moves to {dest_name} include: {', '.join(possible[:5])}."

    return "That move is not legal in this position."


def try_parse_natural_move(message: str, board: chess.Board) -> Tuple[Optional[chess.Move], str]:
    direct = try_parse_san_or_uci(message, board)
    if direct:
        return direct, ""

    text = normalize_move_text(message)

    if "castle kingside" in text or text == "oo":
        for mv in board.legal_moves:
            if board.is_kingside_castling(mv):
                return mv, ""
        return None, "Kingside castling is not legal in this position."

    if "castle queenside" in text or text == "ooo":
        for mv in board.legal_moves:
            if board.is_queenside_castling(mv):
                return mv, ""
        return None, "Queenside castling is not legal in this position."

    to_match = re.search(r"\bto\s+([a-h][1-8])\b", text)
    if to_match:
        dest_token = to_match.group(1)
    else:
        all_squares = re.findall(r"\b([a-h][1-8])\b", text)
        if not all_squares:
            return None, "I could not find the target square."
        dest_token = all_squares[-1]

    try:
        dest_sq = chess.parse_square(dest_token)
    except Exception:
        return None, "Invalid target square."

    piece_type = chess.PAWN
    for name, ptype in PIECE_NAME_TO_TYPE.items():
        if re.search(rf"\b{name}\b", text):
            piece_type = ptype
            break

    promotion_type = None
    promotion_requested = bool(re.search(r"\b(promote|promotion|become|turn into|=)\b", text))
    if not promotion_requested:
        promotion_requested = bool(re.search(r"\b[a-h][1-8]\s+(queen|rook|bishop|knight|q|r|b|n)\b", text))

    if promotion_requested:
        for name, ptype in PROMOTION_NAME_TO_TYPE.items():
            if re.search(rf"\b{name}\b", text):
                promotion_type = ptype
                break

    from_file = None
    from_rank = None
    source_hint = re.search(r"\b(from|on)\s+([a-h][1-8]|[a-h]|[1-8])\b", text)
    if source_hint:
        hint = source_hint.group(2)
        if re.fullmatch(r"[a-h]", hint):
            from_file = hint
        elif re.fullmatch(r"[1-8]", hint):
            from_rank = hint
        elif re.fullmatch(r"[a-h][1-8]", hint):
            from_file = hint[0]
            from_rank = hint[1]

    candidates = []
    for mv in board.legal_moves:
        if mv.to_square != dest_sq:
            continue

        piece = board.piece_at(mv.from_square)
        if not piece:
            continue

        if piece.piece_type != piece_type:
            continue

        from_sq_name = chess.square_name(mv.from_square)
        if from_file and from_sq_name[0] != from_file:
            continue
        if from_rank and from_sq_name[1] != from_rank:
            continue
        if promotion_type is not None and mv.promotion != promotion_type:
            continue

        candidates.append(mv)

    if len(candidates) == 1:
        return candidates[0], ""

    if len(candidates) > 1:
        possible = []
        for mv in candidates:
            try:
                possible.append(board.san(mv))
            except Exception:
                possible.append(mv.uci())
        return None, f"The move is ambiguous. Possible legal moves: {', '.join(possible)}"

    return None, "That move is not legal in this position."


def extract_user_move_candidate(board: chess.Board, user_message: str) -> Dict[str, Any]:
    # Step 1: natural-language intent (already gated by looks_like_move_request)
    # Step 2: convert user text into UCI/SAN candidate(s)
    # Step 3: return candidate move text for frontend legality validation

    normalized = normalize_move_text(user_message)

    # Explicit castling handling so commands like "castle kingside" always
    # produce frontend-ready move_uci/move_san when legal.
    if "castle kingside" in normalized or normalized == "oo":
        for mv in board.legal_moves:
            if board.is_kingside_castling(mv):
                try:
                    san = board.san(mv)
                except Exception:
                    san = mv.uci()
                return {
                    "ok": True,
                    "reply": f"Parsed move candidate: {san}",
                    "action": "move_piece",
                    "move_uci": mv.uci(),
                    "move_san": san,
                    "reasoning": "Parsed kingside castling command. Frontend should validate legality.",
                }

        return {
            "ok": False,
            "reply": "I understood kingside castling, but it is not legal in this position.",
            "action": None,
            "move_uci": None,
            "move_san": None,
            "reasoning": "Kingside castling command detected but no legal kingside castling move found.",
        }

    if "castle queenside" in normalized or normalized == "ooo":
        for mv in board.legal_moves:
            if board.is_queenside_castling(mv):
                try:
                    san = board.san(mv)
                except Exception:
                    san = mv.uci()
                return {
                    "ok": True,
                    "reply": f"Parsed move candidate: {san}",
                    "action": "move_piece",
                    "move_uci": mv.uci(),
                    "move_san": san,
                    "reasoning": "Parsed queenside castling command. Frontend should validate legality.",
                }

        return {
            "ok": False,
            "reply": "I understood queenside castling, but it is not legal in this position.",
            "action": None,
            "move_uci": None,
            "move_san": None,
            "reasoning": "Queenside castling command detected but no legal queenside castling move found.",
        }

    move = try_parse_san_or_uci(normalized, board)
    if move is not None:
        try:
            san = board.san(move)
        except Exception:
            san = move.uci()
        return {
            "ok": True,
            "reply": f"Parsed move candidate: {san}",
            "action": "move_piece",
            "move_uci": move.uci(),
            "move_san": san,
            "reasoning": "Parsed from user text. Frontend should validate legality.",
        }

    # Keep existing natural parser for phrases like "move to d3"
    parsed = _parse_move_intent_from_text(user_message)
    dest_sq = parsed.get("dest_sq")
    piece_type = parsed.get("piece_type", chess.PAWN)
    from_file = parsed.get("from_file")
    from_rank = parsed.get("from_rank")
    promotion_type = parsed.get("promotion_type")

    if dest_sq is None:
        return {
            "ok": False,
            "reply": "I understood this is a move request, but I could not find a valid target square.",
            "action": None,
            "move_uci": None,
            "move_san": None,
            "reasoning": "Move intent detected but destination square could not be extracted.",
        }

    candidates: List[chess.Move] = []
    for mv in board.legal_moves:
        if mv.to_square != dest_sq:
            continue
        piece = board.piece_at(mv.from_square)
        if not piece or piece.piece_type != piece_type:
            continue

        from_sq_name = chess.square_name(mv.from_square)
        if from_file and from_sq_name[0] != from_file:
            continue
        if from_rank and from_sq_name[1] != from_rank:
            continue
        if promotion_type is not None and mv.promotion != promotion_type:
            continue

        candidates.append(mv)

    if len(candidates) == 1:
        mv = candidates[0]
        try:
            san = board.san(mv)
        except Exception:
            san = mv.uci()
        return {
            "ok": True,
            "reply": f"Parsed move candidate: {san}",
            "action": "move_piece",
            "move_uci": mv.uci(),
            "move_san": san,
            "reasoning": "Parsed from natural language. Frontend should validate legality.",
        }

    if len(candidates) > 1:
        possible = []
        for mv in candidates:
            try:
                possible.append(board.san(mv))
            except Exception:
                possible.append(mv.uci())
        return {
            "ok": False,
            "reply": f"I found multiple move candidates to that square: {', '.join(possible)}. Please specify the piece or source square.",
            "action": None,
            "move_uci": None,
            "move_san": None,
            "reasoning": "Ambiguous move request; multiple legal candidates match the parsed destination.",
        }

    # If no legal candidate matched, still return intent as move_piece with null move for frontend fallback.
    return {
        "ok": False,
        "reply": "I understood this is a move request, but could not map it to a unique UCI/SAN move. Please clarify piece and destination.",
        "action": None,
        "move_uci": None,
        "move_san": None,
        "reasoning": "Move intent detected but no unique candidate move could be derived.",
    }


# =========================
# LLM prompts
# =========================
def analysis_system_prompt(response_language: str = "en") -> str:
    return f"""
You are Amy, a helpful, friendly, concise western chess coach assistant for visually impaired users playing on chess.com through HelloChessBot.
User guide (README.md):
{{guide}}
You are given:
- user request
- structured board facts computed by python-chess
- structured Stockfish analysis

Your task:
- Explain the current position naturally and clearly.
- Use the structured board facts and Stockfish analysis as the main truth source.
- Use chat_history to resolve references like "that", "again", "same plan", and follow-up questions.
- Do not invent piece locations, legal moves, or tactical facts.
- Focus on:
  1. whose turn it is
  2. whether there is check, danger, hanging pieces, or pinned pieces
  3. the engine's best move
  4. why that move is recommended
  5. the user's side strengths and weaknesses if user_color is provided
- Adapt explanation depth to the requested level:
  - beginner: simpler, clearer, less jargon
  - intermediate: moderate detail
  - advanced: more concrete chess concepts

Important:
- This route is analysis-only.
- Do not perform action execution.
- Do not ask the frontend to do anything.
- Always write `reply` and `reasoning` in this language code: {response_language}.
- Match the user's style naturally; if response_language is `yue`, use natural Cantonese wording.
- Keep `reply` as plain natural sentences. Avoid markdown and decorative symbols such as `###`, `##`, `**`, `*`, bullet lists, or excessive punctuation.
- Return STRICT JSON ONLY with keys:
{{
  "reply": "...",
  "reasoning": "..."
}}
""".strip()


def general_chat_system_prompt(readme_guide: str, response_language: str = "en") -> str:
    guide = readme_guide or README_FALLBACK_GUIDE
    return f"""
You are Amy, a helpful, friendly, concise western chess coach assistant for visually impaired users playing on chess.com through HelloChessBot.

This route has NO FEN / no current board position.

User guide (README.md):
{guide}

Your tasks:
1. answer the user naturally
2. infer exactly one intent from this list:
{json.dumps(INTENT_LIST, ensure_ascii=False)}
3. keep the reply practical and concise
4. always write `reply` and `reasoning` in language code: {response_language} (if `yue`, use natural Cantonese wording)

Intent meanings:
- start_computer_game: user wants to start a computer game. Return "Starting a computer game now..."
- start_online_game: user wants to start an online game. Return "Starting an online game now..."
- start_puzzle: user wants to start a puzzle. Return "Starting a puzzle now..."
- resign: user wants to resign. Return "Resigning the game now..."
- open_settings: user wants to open settings. Return "Opening settings now..."
- login: user wants to log in. Return "Logging in now..."
- logout: user wants to log out. Return "Logging out now..."
- return_home: user wants to return to the home page. Return "Returning to the home page now..."
- undo_last_move: user wants to undo the last move. Return "Undoing the last move now..."
- move_piece: user tries to make a move.
- ask_situation: user asks about board situation, but there is no board context
- ask_help: user asks how to use the app / what you can do. Return an answer by looking up relevant guidance in README.md and responding with the most relevant, concise instructions.
- unknown: anything else or ambiguous

Rules:
- Use chat_history to resolve follow-ups and references (e.g. "again", "that", "same as before").
- If the user asks about the current position or best move but there is no FEN, choose intent = ask_situation and briefly ask for the FEN.
- If the user asks to move a piece but there is no FEN, choose intent = move_piece and explain that you need the current FEN.
- If the user request is ambiguous, choose unknown.
- Keep `reply` as plain natural sentences. Avoid markdown and decorative symbols such as `###`, `##`, `**`, `*`, bullet lists, or excessive punctuation.
- Return STRICT JSON ONLY with keys:
{{
  "reply": "...",
  "intent": "...",
  "reasoning": "..."
}}
""".strip()


def in_game_chat_system_prompt(response_language: str = "en") -> str:
    return f"""
You are Amy, a helpful, friendly, concise western chess coach assistant for visually impaired users playing on chess.com through HelloChessBot.

You are given:
- user message
- structured board facts computed by python-chess
- structured Stockfish analysis

These structured references are more reliable than your own assumptions.
Use them to reduce hallucinations.

Your tasks:
1. answer the user's question naturally
2. infer exactly one intent from this list:
{json.dumps(INTENT_LIST, ensure_ascii=False)}
3. always write `reply` and `reasoning` in language code: {response_language} (if `yue`, use natural Cantonese wording)

Intent meanings:
- start_computer_game: user wants to start a computer game. Return "Starting a computer game now..."
- start_online_game: user wants to start an online game. Return "Starting an online game now..."
- start_puzzle: user wants to start a puzzle. Return "Starting a puzzle now..."
- resign: user wants to resign. Return "Resigning the game now..."
- open_settings: user wants to open settings. Return "Opening settings now..."
- login: user wants to log in. Return "Logging in now..."
- undo_last_move: user wants to undo the last move. Return "Undoing the last move now..."
- logout: user wants to log out. Return "Logging out now..."
- return_home: user wants to return to the home page. Return "Returning to the home page now..."
- move_piece: user tries to make a move.
- ask_situation: user asks about board situation, but there is no board context
- ask_help: user asks how to use the app / what you can do. Return an answer by looking up relevant guidance in README.md and responding with the most relevant, concise instructions.
- unknown: anything else or ambiguous

- Use chat_history to resolve short follow-ups such as:
  "yes", "no", "ok", "okay", "why?", "tell me more", "move it", "make this move".
- If the previous assistant message recommended a best move and the user asks
  for more information, explain that same move in more detail instead of repeating
  the same summary.
- If the previous assistant message recommended a best move and the user confirms
  they want to play it, set intent = move_piece.
- Avoid repeating the exact same explanation unless the user explicitly asks you to repeat it.

Rules:
- Use chat_history to resolve follow-ups and references (e.g. "again", "that move", "same plan").
- This route is NOT responsible for executing user moves.
- Do not provide candidate moves for execution.
- If the user asks about the current position, best move, danger, or evaluation, set intent = ask_situation.
- If the user is asking a general question during a game, answer naturally.
- Do not invent piece locations or legal moves.
- Keep `reply` as plain natural sentences. Avoid markdown and decorative symbols such as `###`, `##`, `**`, `*`, bullet lists, or excessive punctuation.
- Return STRICT JSON ONLY with keys:
{{
  "reply": "...",
  "intent": "...",
  "reasoning": "..."
}}
""".strip()

CONFIRM_MOVE_PATTERNS = {
    "yes",
    "ok",
    "okay",
    "do it",
    "move it",
    "make move",
    "make that move",
    "yes i want to make this move",
    "i want to make this move",
    "play it",
    "yes play it",
}

MORE_INFO_PATTERNS = [
    r"\bmore information\b",
    r"\bmore details\b",
    r"\btell me more\b",
    r"\bwhy\b",
    r"\bexplain\b",
    r"\bhow is it strong\b",
    r"\bwhy is it a strong choice\b",
]
QUESTION_STARTERS = {
    "what", "which", "where", "why", "how",
    "can", "could", "would", "should",
    "who", "when", "is", "are", "do", "does"
}
QUESTION_HINT_PATTERNS = [
    r"\bwhat can i move\b",
    r"\bwhat move can i make\b",
    r"\bwhat position can i move\b",
    r"\bwhich piece can i move\b",
    r"\bwhere can i move\b",
    r"\bwhat are my legal moves\b",
    r"\bwhat legal moves\b",
    r"\bwhat moves are available\b",
    r"\bwhat is the use of\b",
    r"\bhow do i use\b",
]
def is_confirming_previous_move(text: str) -> bool:
    """
    Only treat very short, explicit confirmations as confirmation.
    Do NOT use substring search, otherwise sentences like
    'okay so what position can i move right now'
    will be misread as confirmation.
    """
    text = normalize_chess_speech_text(text).strip()
    return text in CONFIRM_MOVE_PATTERNS

def is_asking_for_more_info(text: str) -> bool:
    text = normalize_chess_speech_text(text)
    return any(re.search(p, text) for p in MORE_INFO_PATTERNS)


def looks_like_question(message: str) -> bool:
    raw = (message or "").strip().lower()
    text = normalize_chess_speech_text(message)

    if "?" in raw:
        return True

    tokens = text.split()
    first_word = tokens[0] if tokens else ""
    if first_word in QUESTION_STARTERS:
        return True

    for pattern in QUESTION_HINT_PATTERNS:
        if re.search(pattern, text):
            return True

    return False


def looks_like_move_request(message: str) -> bool:
    """
    Strong rule:
    - explicit UCI / SAN / castling => move request
    - natural language move request => must NOT be a question
    - questions like 'what can i move right now' must return False
    """
    text = normalize_chess_speech_text(message)

    # Explicit coordinate move: e2e4 / e7e8q
    if re.fullmatch(r"[a-h][1-8][a-h][1-8][qrbn]?", text):
        return True

    # Space-separated UCI: "b2 b4" / "e7 e8 q"
    if re.fullmatch(r"[a-h][1-8]\s+[a-h][1-8](?:\s*[qrbn])?", text):
        return True

    # SAN-like move: Nf3 / Qxd4 / exd5 / e8=Q / O-O
    if re.fullmatch(r"[nbrqk]?[a-h]?[1-8]?x?[a-h][1-8](=[nbrq])?[+#]?", text):
        return True

    if text in {"oo", "ooo", "castle kingside", "castle queenside"}:
        return True

    # If it is a question, do not treat it as move request.
    if looks_like_question(text):
        return False

    words = set(text.split())
    has_square = bool(re.search(r"\b[a-h][1-8]\b", text))
    has_move_verb = bool(words & MOVE_VERBS)
    has_piece_word = bool(words & set(PIECE_NAME_TO_TYPE.keys()))

    # Natural language move requests:
    # e.g. "move to e4", "move my knight to d5", "queen takes d4"
    if has_square and has_move_verb:
        return True

    if has_square and has_piece_word and re.search(r"\b(?:to|from|take|takes|capture|captures|on)\b", text):
        return True

    return False
def should_store_pending_move(response: ChatResponse) -> bool:
    """
    Only store a pending move when the assistant is clearly giving
    a board-related recommendation, not for every in-game reply.
    """
    if not getattr(response, "engine_analysis", None):
        return False

    if getattr(response, "action", None) == "move_piece":
        return False

    if getattr(response, "intent", None) != "ask_situation":
        return False

    best_uci = response.engine_analysis.get("best_move_uci")
    best_san = response.engine_analysis.get("best_move_san")
    if not best_uci or not best_san:
        return False

    reply = (getattr(response, "reply", "") or "").lower()
    best_san_l = str(best_san).lower()

    recommendation_cues = [
        # English
        "best move",
        "recommended move",
        "i would play",
        "i'd play",
        "consider",
        "strong move",
        "best continuation",
        # Chinese (simplified + traditional)
        "最佳着",
        "最佳著",
        "推荐",
        "推薦",
        "建议走",
        "建議走",
        "我会走",
        "我會走",
        "可以考虑",
        "可以考慮",
        "较强的一步",
        "較強的一步",
        # Cantonese
        "建議你行",
        "我會行",
        "最好嘅一步",
        "最好的一步",
    ]
    if best_san_l in reply:
        return True

    return any(cue in reply for cue in recommendation_cues)


def translate_move_request_to_english(user_message: str) -> Dict[str, Any]:
    payload = {
        "task": "detect_move_intent_and_translate_to_english_chess_command",
        "user_message": user_message,
    }

    system_prompt = """
You are a strict JSON function for chess move-command preprocessing.
Given a user message in any language (including Cantonese and Mandarin), do the following:
1) Detect whether the user intent is to move a chess piece now.
2) If yes, convert the move command into a short English chess command suitable for downstream parsing.

Output STRICT JSON only:
{
  "is_move_intent": true/false,
  "english_move_text": "...",
  "reasoning": "..."
}

Rules:
- If move intent is true, english_move_text must be a compact actionable move command in English,
  e.g. "pawn to e4", "knight f3", "bishop takes c4", "castle kingside", "e2e4".
- If move intent is false, english_move_text must be empty string.
- Do not output markdown.
""".strip()

    result = call_replicate_json(
        system_prompt=system_prompt,
        payload=payload,
        max_tokens=120,
        temperature=0,
    )

    is_move_intent = bool(result.get("is_move_intent", False))
    english_move_text = str(result.get("english_move_text", "") or "").strip()

    if not is_move_intent:
        english_move_text = ""

    return {
        "is_move_intent": is_move_intent,
        "english_move_text": english_move_text,
        "reasoning": result.get("reasoning"),
    }

# =========================
# LLM callers
# =========================
def call_replicate_json(
    system_prompt: str,
    payload: Dict[str, Any],
    max_tokens: int = 500,
    temperature: float = 0.2,
) -> Dict[str, Any]:
    model_ref = "openai/gpt-5.2"
    max_attempts = 3

    for attempt in range(1, max_attempts + 1):
        try:
            output = replicate_client.run(
                model_ref,
                input={
                    "prompt": json.dumps(payload, ensure_ascii=False),
                    "system_prompt": system_prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9,
                },
            )

            if isinstance(output, list):
                text = "".join(str(x) for x in output).strip()
            else:
                text = str(output).strip()

            logger.info("Replicate raw output: %s", text[:1500])
            return safe_json_loads(text)

        except ReplicateError as e:
            is_429 = getattr(e, "status", None) == 429 or "status: 429" in str(e)
            if is_429 and attempt < max_attempts:
                wait_seconds = min(2 ** attempt, 8)
                logger.warning(
                    "Replicate rate-limited (429). Retry %s/%s in %ss",
                    attempt,
                    max_attempts,
                    wait_seconds,
                )
                time.sleep(wait_seconds)
                continue

            if is_429:
                logger.warning("Replicate still rate-limited after retries: %s", e)
                return {
                    "reply": "目前請求太多，我這邊被暫時限流。請約 5 秒後再試一次。",
                    "intent": "unknown",
                    "reasoning": "Replicate API rate limited (429).",
                }

            logger.exception("Failed to call replicate")
            return {
                "reply": "Sorry, I ran into an issue while replying. Please try again later.",
                "intent": "unknown",
                "reasoning": "Replicate call failed.",
            }

        except Exception:
            logger.exception("Failed to call replicate")
            return {
                "reply": "Sorry, I ran into an issue while replying. Please try again later.",
                "intent": "unknown",
                "reasoning": "Replicate call failed.",
            }

    return {
        "reply": "目前服務忙碌中，請稍後再試。",
        "intent": "unknown",
        "reasoning": "Replicate call exhausted retries.",
    }


def call_analysis_llm(
    user_message: str,
    level: str,
    user_color: Optional[str],
    board_facts: Dict[str, Any],
    engine_analysis: Dict[str, Any],
    response_language: str = "en",
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    payload = {
        "route": "analysis",
        "level": level,
        "user_color": user_color,
        "user_message": user_message,
        "chat_history": chat_history or [],
        "board_facts": board_facts,
        "engine_analysis": engine_analysis,
        "response_language": response_language,
    }
    return call_replicate_json(
        system_prompt=analysis_system_prompt(response_language=response_language),
        payload=payload,
        max_tokens=700,
        temperature=0.2,
    )


def call_general_chat_llm(
    user_message: str,
    level: str,
    response_language: str = "en",
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    payload = {
        "route": "normal_chat",
        "level": level,
        "user_message": user_message,
        "chat_history": chat_history or [],
        "response_language": response_language,
    }
    return call_replicate_json(
        system_prompt=general_chat_system_prompt(README_GUIDE, response_language=response_language),
        payload=payload,
        max_tokens=450,
        temperature=0.3,
    )


def call_in_game_chat_llm(
    user_message: str,
    level: str,
    user_color: Optional[str],
    board_facts: Dict[str, Any],
    engine_analysis: Dict[str, Any],
    response_language: str = "en",
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    payload = {
        "route": "in_game_chat",
        "level": level,
        "user_color": user_color,
        "user_message": user_message,
        "chat_history": chat_history or [],
        "board_facts": board_facts,
        "engine_analysis": engine_analysis,
        "response_language": response_language,
    }
    return call_replicate_json(
        system_prompt=in_game_chat_system_prompt(response_language=response_language),
        payload=payload,
        max_tokens=650,
        temperature=0.2,
    )


# =========================
# Route handlers
# =========================
def handle_analysis_route(
    req: ChatRequest,
    response_language: str = "en",
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> ChatResponse:
    if not req.fen:
        return ChatResponse(
            ok=False,
            mode="analysis",
            reply="Please provide the current FEN so I can analyze the position.",
            intent="ask_situation",
            action="ask_situation",
            reasoning="Analysis route requires FEN.",
        )

    board = chess.Board(req.fen)
    board_facts = compute_board_facts(board, req.user_color)
    engine_analysis = analyze_with_stockfish(board, req.depth, req.multipv)

    user_message = strip_analysis_prefix(req.message)
    if not user_message:
        user_message = ""

    llm_result = call_analysis_llm(
        user_message=user_message,
        level=req.level,
        user_color=req.user_color,
        board_facts=board_facts,
        engine_analysis=engine_analysis,
        response_language=response_language,
        chat_history=chat_history,
    )

    reply = first_non_empty(
        llm_result.get("reply"),
        "I analyzed the position.",
    ) or "I analyzed the position."

    return ChatResponse(
        ok=True,
        mode="analysis",
        reply=reply,
        intent="ask_situation",
        action=None,
        reasoning=llm_result.get("reasoning"),
        board_facts=board_facts,
        engine_analysis=engine_analysis,
    )


def handle_normal_chat_route(
    req: ChatRequest,
    response_language: str = "en",
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> ChatResponse:
    llm_result = call_general_chat_llm(
        user_message=req.message,
        level=req.level,
        response_language=response_language,
        chat_history=chat_history,
    )

    intent = str(llm_result.get("intent", "unknown")).strip()
    if intent not in INTENT_LIST:
        intent = "unknown"

    reply = resolve_intent_reply(
        intent,
        llm_result.get("reply"),
        move_piece_needs_detail=True,
        ask_situation_needs_fen=True,
    )

    return ChatResponse(
        ok=True,
        mode="normal_chat",
        reply=reply,
        intent=intent,
        action=map_intent_to_action(intent),
        reasoning=llm_result.get("reasoning"),
        board_facts=None,
        engine_analysis=None,
    )

def handle_in_game_chat_route(
    req: ChatRequest,
    response_language: str = "en",
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> ChatResponse:
    if not req.fen:
        raise ValueError("In-game chat route requires FEN.")

    board = chess.Board(req.fen)
    board_facts = compute_board_facts(board, req.user_color)
    engine_analysis = analyze_with_stockfish(board, req.depth, req.multipv)

    normalized_message = preprocess_user_message(req.message)

    pending_move = None
    with SESSIONS_LOCK:
        session_state = SESSIONS.get(req.session_id)
        if session_state is not None:
            pending_move = session_state.get("pending_move")

    same_position_pending_move = (
        pending_move
        and pending_move.get("move_uci")
        and pending_move.get("move_san")
        and pending_move.get("fen") == req.fen
    )

    # Only confirm previous recommended move if:
    # 1) there is a pending move
    # 2) it belongs to the current FEN
    # 3) the new user message is a short explicit confirmation
    # 4) the new user message is NOT a question
    if (
        same_position_pending_move
        and not looks_like_question(normalized_message)
        and is_confirming_previous_move(normalized_message)
    ):
        return ChatResponse(
            ok=True,
            mode="in_game_chat",
            reply=f"Okay, playing {pending_move['move_san']} now.",
            intent="move_piece",
            action="move_piece",
            move_uci=pending_move["move_uci"],
            move_san=pending_move["move_san"],
            candidate_move_raw=pending_move["move_san"],
            candidate_move_uci=pending_move["move_uci"],
            candidate_move_san=pending_move["move_san"],
            reasoning="User explicitly confirmed the previously recommended move.",
            board_facts=board_facts,
            engine_analysis=engine_analysis,
        )

    # If it looks like a real move request, parse it directly.
    # Questions such as:
    # - what can i move right now
    # - which piece can i move
    # should not come here anymore.
    if looks_like_move_request(normalized_message):
        english_move_text = normalized_message
        translation_reasoning = None

        # Fast local path: if user text already contains explicit from/to squares,
        # parse directly to avoid an extra translation LLM call (reduces 429 risk).
        direct_square_move = try_extract_move_from_square_path(normalized_message, board)
        if direct_square_move is not None:
            try:
                direct_san = board.san(direct_square_move)
            except Exception:
                direct_san = direct_square_move.uci()

            return ChatResponse(
                ok=True,
                mode="in_game_chat",
                reply=f"Parsed move candidate: {direct_san}",
                intent="move_piece",
                action="move_piece",
                move_uci=direct_square_move.uci(),
                move_san=direct_san,
                candidate_move_raw=direct_san,
                candidate_move_uci=direct_square_move.uci(),
                candidate_move_san=direct_san,
                reasoning="Parsed direct square path from user message without translation LLM call.",
                board_facts=board_facts,
                engine_analysis=engine_analysis,
            )

        # When user uses non-English input (e.g. Cantonese / Mandarin),
        # translate move command to English first, then execute existing parser logic.
        if response_language in {"zh-cn", "zh-tw", "yue"}:
            translated = translate_move_request_to_english(normalized_message)
            if translated.get("is_move_intent") and translated.get("english_move_text"):
                english_move_text = preprocess_user_message(str(translated["english_move_text"]))
                translation_reasoning = translated.get("reasoning")

        parsed = extract_user_move_candidate(
            board=board,
            user_message=english_move_text,
        )

        merged_reasoning = parsed.get("reasoning")
        if translation_reasoning:
            merged_reasoning = (
                f"{merged_reasoning} | Move command translated to English before parsing. "
                f"Translator note: {translation_reasoning}"
            )

        return ChatResponse(
            ok=True,
            mode="in_game_chat",
            reply=parsed["reply"],
            intent="move_piece",
            action="move_piece" if parsed.get("move_uci") else None,
            move_uci=parsed.get("move_uci"),
            move_san=parsed.get("move_san"),
            candidate_move_raw=english_move_text,
            candidate_move_uci=parsed.get("move_uci"),
            candidate_move_san=parsed.get("move_san"),
            reasoning=merged_reasoning,
            board_facts=board_facts,
            engine_analysis=engine_analysis,
        )

    # Otherwise let the LLM handle explanation / help / board chat.
    llm_result = call_in_game_chat_llm(
        user_message=normalized_message,
        level=req.level,
        user_color=req.user_color,
        board_facts=board_facts,
        engine_analysis=engine_analysis,
        response_language=response_language,
        chat_history=chat_history,
    )

    intent = str(llm_result.get("intent", "unknown")).strip()
    if intent not in INTENT_LIST:
        intent = "unknown"

    reply = resolve_intent_reply(intent, llm_result.get("reply"))

    # LLM may classify intent as move_piece without returning explicit move coordinates.
    # Try multiple sources in priority order and keep the first parseable concrete move.
    if intent == "move_piece":
        translation_reasoning = None
        parser_source = "user_message"

        # 1) Try user message directly.
        parsed = extract_user_move_candidate(
            board=board,
            user_message=normalized_message,
        )
        candidate_raw = normalized_message

        # 2) If failed, try move extraction from LLM reply text (often contains g3/e4 etc.).
        llm_reply_text = preprocess_user_message(str(llm_result.get("reply", "") or ""))
        if not parsed.get("move_uci") and llm_reply_text:
            parsed_from_reply = extract_user_move_candidate(
                board=board,
                user_message=llm_reply_text,
            )
            if parsed_from_reply.get("move_uci"):
                parsed = parsed_from_reply
                candidate_raw = llm_reply_text
                parser_source = "llm_reply"

        # 3) If still failed and language is zh/yue, translate to English then parse.
        if not parsed.get("move_uci") and response_language in {"zh-cn", "zh-tw", "yue"}:
            translated = translate_move_request_to_english(normalized_message)
            if translated.get("is_move_intent") and translated.get("english_move_text"):
                english_move_text = preprocess_user_message(str(translated["english_move_text"]))
                parsed_from_en = extract_user_move_candidate(
                    board=board,
                    user_message=english_move_text,
                )
                translation_reasoning = translated.get("reasoning")
                if parsed_from_en.get("move_uci"):
                    parsed = parsed_from_en
                    candidate_raw = english_move_text
                    parser_source = "translated_english"

        # 4) If still failed, fallback to same-position pending move.
        if not parsed.get("move_uci") and same_position_pending_move:
            parsed = {
                "move_uci": pending_move["move_uci"],
                "move_san": pending_move["move_san"],
                "reasoning": "Used same-position pending recommended move as fallback.",
            }
            candidate_raw = pending_move["move_san"]
            parser_source = "pending_move"

        merged_reasoning = llm_result.get("reasoning")
        if translation_reasoning:
            merged_reasoning = (
                f"{merged_reasoning} | Move command translated to English before parsing. "
                f"Translator note: {translation_reasoning}"
            )

        if parsed.get("reasoning"):
            merged_reasoning = f"{merged_reasoning} | Parser source={parser_source}. Parser note: {parsed.get('reasoning')}"

        return ChatResponse(
            ok=True,
            mode="in_game_chat",
            reply=reply,
            intent="move_piece",
            action="move_piece" if parsed.get("move_uci") else None,
            move_uci=parsed.get("move_uci"),
            move_san=parsed.get("move_san"),
            candidate_move_raw=candidate_raw,
            candidate_move_uci=parsed.get("move_uci"),
            candidate_move_san=parsed.get("move_san"),
            reasoning=merged_reasoning,
            board_facts=board_facts,
            engine_analysis=engine_analysis,
        )

    return ChatResponse(
        ok=True,
        mode="in_game_chat",
        reply=reply,
        intent=intent,
        action=map_intent_to_action(intent),
        candidate_move_raw=None,
        candidate_move_uci=None,
        candidate_move_san=None,
        reasoning=llm_result.get("reasoning"),
        board_facts=board_facts,
        engine_analysis=engine_analysis,
    )
# =========================
# Routes
# =========================
@app.get("/")
def root():
    return {
        "message": "HelloChessBot Chat API is running",
        "replicate_loaded": bool(REPLICATE_API_TOKEN),
        "stockfish_path": STOCKFISH_PATH,
        "app_api_key_loaded": bool(APP_API_KEY),
        "stt_loaded": STT_MODEL is not None,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, authorization: Optional[str] = Header(default=None)):
    if APP_API_KEY:
        if not authorization or authorization != f"Bearer {APP_API_KEY}":
            raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        session_id = _normalized_session_id(req.session_id)
        session_state = get_or_create_session(session_id)
        with SESSIONS_LOCK:
            history_deque = session_state["history"]
            chat_history = list(history_deque)
            session_preferred_language = session_state.get("preferred_language")
        logger.debug("Session %s history preview:\n%s", session_id, _format_history_for_prompt(chat_history))

        # normalize once at the API entry point
        normalized_message = preprocess_user_message(req.message)
        req = req.model_copy(update={"message": normalized_message, "session_id": session_id})

        if is_analysis_prompt(req.message):
            # Analysis trigger text is often English (e.g. "code 8888 ...").
            # Prefer latest user-history language over stale session preference.
            inferred_from_history = infer_preferred_language_from_history(chat_history)
            history_lang = normalize_language_code(inferred_from_history, text_hint="")
            session_lang = normalize_language_code(session_preferred_language, text_hint="")

            if history_lang != "unknown" and history_lang in SUPPORTED_RESPONSE_LANGUAGES:
                response_language = history_lang
            elif session_lang != "unknown" and session_lang in SUPPORTED_RESPONSE_LANGUAGES:
                response_language = session_lang
            else:
                content_wo_prefix = strip_analysis_prefix(req.message)
                response_language = choose_response_language(
                    stt_language=None,
                    message=content_wo_prefix,
                    session_preferred_language=session_preferred_language,
                )
                if response_language not in SUPPORTED_RESPONSE_LANGUAGES:
                    response_language = "en"
        else:
            response_language = choose_response_language(
                stt_language=None,
                message=req.message,
                session_preferred_language=session_preferred_language,
            )
            if response_language not in SUPPORTED_RESPONSE_LANGUAGES:
                response_language = "en"

        if response_language in SUPPORTED_RESPONSE_LANGUAGES:
            with SESSIONS_LOCK:
                live_session = SESSIONS.get(session_id)
                if live_session is not None:
                    live_session["preferred_language"] = response_language

        logger.info(
            "[chat] session_id=%s | user_message=%s | response_language=%s",
            session_id,
            req.message,
            response_language,
        )

        # Route 1: analysis mode
        if is_analysis_prompt(req.message):
            response = handle_analysis_route(req, response_language=response_language, chat_history=chat_history)
        # Route 3: in-game chat with FEN
        elif req.fen:
            response = handle_in_game_chat_route(req, response_language=response_language, chat_history=chat_history)
        # Route 2: normal chat without FEN
        else:
            response = handle_normal_chat_route(req, response_language=response_language, chat_history=chat_history)

        if getattr(response, "intent", None) == "move_piece":
            logger.info(
                "[chat->frontend] intent=move_piece | action=%s | move_uci=%s | move_san=%s | candidate_raw=%s | candidate_uci=%s | candidate_san=%s",
                getattr(response, "action", None),
                getattr(response, "move_uci", None),
                getattr(response, "move_san", None),
                getattr(response, "candidate_move_raw", None),
                getattr(response, "candidate_move_uci", None),
                getattr(response, "candidate_move_san", None),
            )

        with SESSIONS_LOCK:
            live_session = SESSIONS.get(session_id)
            if live_session is not None:
                # Store pending move only when the assistant is clearly recommending one.
                if req.fen and should_store_pending_move(response):
                    best_uci = response.engine_analysis.get("best_move_uci")
                    best_san = response.engine_analysis.get("best_move_san")

                    live_session["pending_move"] = {
                        "move_uci": best_uci,
                        "move_san": best_san,
                        "fen": req.fen,
                    }
                # Clear pending move once an actual move execution is returned.
                elif getattr(response, "action", None) == "move_piece" and getattr(response, "move_uci", None):
                    live_session["pending_move"] = None
                # If user is no longer in a game, also clear it.
                elif not req.fen:
                    live_session["pending_move"] = None

                user_msg_for_history = (req.message or "").strip()
                if user_msg_for_history:
                    live_session["history"].append({"role": "user", "content": user_msg_for_history})

                assistant_msg_for_history = (response.reply or "").strip()
                if assistant_msg_for_history:
                    live_session["history"].append({"role": "assistant", "content": assistant_msg_for_history})

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Chat route failed")
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")


@app.post("/stt")
async def stt(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(default=None),
):
    if APP_API_KEY:
        if not authorization or authorization != f"Bearer {APP_API_KEY}":
            raise HTTPException(status_code=401, detail="Unauthorized")

    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        stt_model = ensure_stt_model_loaded()
        if stt_model is None:
            return {
                "text": "",
                "raw_text": "",
                "duration_seconds": None,
                "warning": "STT model not loaded on server",
            }

        # Primary path: use VAD for better segmentation.
        # Fallback path: disable VAD when onnxruntime/numpy in the environment is broken.
        transcribe_kwargs = dict(
            beam_size=5,
            condition_on_previous_text=False,
            task="transcribe",
            initial_prompt=(
                "Chess voice commands in multiple languages. Common terms include: "
                "knight, bishop, rook, queen, king, pawn, "
                "castle kingside, castle queenside, move to e4, knight f3, bishop c4, rook e1, "
                "马, 象, 车, 后, 王, 兵, 王车易位, 馬, 象, 車, 后, 王, 兵, 王車易位."
            ),
        )

        try:
            segments, info = stt_model.transcribe(
                tmp_path,
                vad_filter=True,
                **transcribe_kwargs,
            )
        except Exception as transcribe_err:
            err_msg = str(transcribe_err)
            if (
                "onnxruntime" in err_msg.lower()
                or "vad filter" in err_msg.lower()
                or "import numpy failed" in err_msg.lower()
            ):
                logger.warning(
                    "STT VAD unavailable (%s). Retrying without VAD.",
                    err_msg,
                )
                segments, info = stt_model.transcribe(
                    tmp_path,
                    vad_filter=False,
                    **transcribe_kwargs,
                )
            else:
                raise

        raw_text = "".join(seg.text for seg in segments).strip()
        normalized_text = normalize_chess_speech_text(raw_text)

        detected_language = normalize_language_code(
            getattr(info, "language", None),
            text_hint=raw_text,
        )
        detected_language = normalize_stt_input_language(detected_language)

        # Restrict STT accepted input languages to: English, Mandarin, Cantonese.
        # Whisper language-id may occasionally mis-detect short/noisy speech
        # (e.g. detect 'nn' while transcript is clearly English).
        # So we add a text-based fallback before rejecting.
        if detected_language not in SUPPORTED_STT_INPUT_LANGUAGES:
            text_based_language = detect_text_language(raw_text)
            text_based_language = normalize_stt_input_language(text_based_language)
            if text_based_language in SUPPORTED_STT_INPUT_LANGUAGES:
                logger.warning(
                    "STT language-id mismatch: detected=%s, text_based=%s. "
                    "Accepting by text fallback.",
                    detected_language,
                    text_based_language,
                )
                detected_language = text_based_language
            else:
                logger.info(
                    "Reject STT input: detected=%s, text_based=%s, raw_text=%s",
                    detected_language,
                    text_based_language,
                    raw_text,
                )
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Unsupported STT input language. "
                        "Only English, Mandarin Chinese, and Cantonese are allowed."
                    ),
                )

        response_language = choose_response_language(
            stt_language=detected_language,
            message=raw_text,
            session_preferred_language=None,
        )
        if response_language not in SUPPORTED_RESPONSE_LANGUAGES:
            response_language = "en"

        return {
            "text": normalized_text,
            "raw_text": raw_text,
            "corrections_applied": normalized_text != raw_text,
            "duration_seconds": getattr(info, "duration", None),
            "language": detected_language,
            "response_language": response_language,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("STT failed")
        raise HTTPException(status_code=500, detail=f"STT failed: {e}")

    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

