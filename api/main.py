import json
import os
import secrets
import threading

from fastapi import FastAPI, Header, HTTPException
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

app = FastAPI()

# --- Configuration (tout vient de l'environnement Vercel) -------------------
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
THINKING_BUDGET = int(os.environ.get("GEMINI_THINKING_BUDGET", "0"))  # 0 = off, -1 = auto

# Exemple : PROXY_TOKENS='{"token_perso": null, "token_ami": 100}'
# null = illimité, un entier = nombre max de requêtes
TOKENS: dict[str, int | None] = json.loads(os.environ["PROXY_TOKENS"])

usage = {t: 0 for t in TOKENS}
usage_lock = threading.Lock()


# --- Authentification et quota ------------------------------------------------
def verifier_token(recu: str) -> str:
    """Renvoie le token connu correspondant, ou lève 401. Temps constant."""
    trouve = None
    for connu in TOKENS:  # pas de break : même durée que le token soit bon ou non
        if secrets.compare_digest(recu.encode(), connu.encode()):
            trouve = connu
    if trouve is None:
        raise HTTPException(status_code=401, detail="invalid token")
    return trouve


def verifier_quota(token: str) -> None:
    limite = TOKENS[token]
    with usage_lock:
        if limite is not None and usage[token] >= limite:
            raise HTTPException(status_code=403, detail="token usage limit reached")


def compter_usage(token: str) -> int | None:
    """Incrémente après un appel réussi. Renvoie le nombre restant (None = illimité)."""
    limite = TOKENS[token]
    with usage_lock:
        usage[token] += 1
        return None if limite is None else max(0, limite - usage[token])


# --- Appel Gemini ----------------------------------------------------------------
def run_gemini(prompt: str, temperature: float | None, json_mode: bool) -> str:
    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=THINKING_BUDGET),
        temperature=temperature,
        response_mime_type="application/json" if json_mode else None,
    )
    try:
        response = client.models.generate_content(
            model=MODEL, contents=prompt, config=config
        )
    except errors.APIError as e:
        code = getattr(e, "code", None)
        status = 429 if code == 429 else 502
        raise HTTPException(status_code=status, detail=f"gemini error {code}")
    except Exception:
        raise HTTPException(status_code=502, detail="gemini unreachable")

    if not response.text:
        raise HTTPException(status_code=502, detail="empty response from gemini")
    return response.text


def repondre(token_recu: str, prompt: str, temperature: float | None, json_mode: bool):
    token = verifier_token(token_recu)
    verifier_quota(token)
    answer = run_gemini(prompt, temperature, json_mode)
    restant = compter_usage(token)
    return {"answer": answer, "remaining_prompt": restant}


# --- Endpoints ---------------------------------------------------------------------
class AskBody(BaseModel):
    prompt: str = Field(min_length=1, max_length=50_000)
    temperature: float | None = Field(default=None, ge=0, le=2)
    json_mode: bool = False


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ask")  # ancien format, conservé pour le bot WhatsApp
def ask_get(prompt: str, token: str):
    return repondre(token, prompt, None, False)


@app.post("/ask")
def ask_post(body: AskBody, authorization: str = Header(...)):
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="missing bearer token")
    return repondre(token, body.prompt, body.temperature, body.json_mode)
