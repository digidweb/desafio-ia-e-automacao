"""API de classificação de mensagens de clientes com IA (Google Gemini)."""
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from . import gemini
from .schemas import ClassificacaoResposta, MensagemEntrada

load_dotenv()

app = FastAPI(
    title="Classificador de Mensagens de Clientes",
    description="Recebe mensagens de clientes e usa IA para classificar categoria, "
                "setor, urgência e sentimento, devolvendo um JSON estruturado.",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {"status": "ok", "modelo": gemini.modelo_configurado()}


@app.post("/classificar", response_model=ClassificacaoResposta)
def classificar(entrada: MensagemEntrada):
    try:
        resultado = gemini.classificar(entrada.nome, entrada.mensagem)
    except gemini.ErroIA as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ClassificacaoResposta(cliente=entrada, classificacao=resultado,
                                 modelo=gemini.modelo_configurado())
