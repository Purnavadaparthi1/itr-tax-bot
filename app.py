#app.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ctransformers import AutoModelForCausalLM
from rag_engine import retrieve_context

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Load TinyLlama
llm = AutoModelForCausalLM.from_pretrained(
    "model",
    model_file="tinyllama.gguf",
    model_type="llama",
    context_length=2048
)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    question = data.get("question")

    result = retrieve_context(question)

    # ✅ Structured answers → return directly (NO LLM)
    if result and not result.startswith("RAG::"):
        return {"answer": result}

    # 🤖 RAG answers → use LLM only for formatting
    if result and result.startswith("RAG::"):
        context = result.replace("RAG::", "")

        prompt = f"""
You are a strict HR assistant.
Answer ONLY from the context.
If not found, say: Information not available.

Context:
{context}

Question: {question}

Answer:
"""

        answer = llm(
            prompt,
            max_new_tokens=80,
            temperature=0.0
        )

        return {"answer": answer.strip()}

    return {"answer": "Information not available."}
