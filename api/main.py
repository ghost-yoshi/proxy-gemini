from fastapi import FastAPI, Request, Header, HTTPException
from google import genai
import os

app = FastAPI()

# Clé Gemini stockée UNIQUEMENT sur Vercel
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

pToken = 'yoshi2411107?GST Yoshi !444'
TOKENS = {
    'yoshi241107wed2417': 0,
    "yoshi24511017wed": 0,
    pToken : 0
}
MaxUsagePerToken = 100

@app.get("/ask")
def ask_gemini(
    prompt: str,
    token: str ):

    if token == pToken:
        MaxUsagePerToken = 99999999999


    if (token not in TOKENS):
        raise HTTPException(status_code=401, detail="invalid token")
    
    #count
    if TOKENS[token] >= MaxUsagePerToken or token != pToken:
        raise HTTPException(status_code=403, detail="token usage limit reached")

    #incrementation
    TOKENS[token] += 1

    #gemini call

    response = client.models.generate_content(
        model = "gemini-2.5-flash",
        contents=prompt
    )

    remainingPrompt = MaxUsagePerToken - TOKENS[token]
    return {
            "answer": response.text,
            "remaining prompt": remainingPrompt

        }
