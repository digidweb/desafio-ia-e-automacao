"""Cliente mínimo da API REST do Google Gemini (generateContent)."""
import json
import os
import time

import httpx
from pydantic import ValidationError

from .prompt import SYSTEM_PROMPT, montar_prompt_usuario
from .schemas import Classificacao

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Schema enviado ao Gemini para forçar a saída em JSON estruturado
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "categoria": {"type": "STRING", "enum": ["duvida", "reclamacao", "solicitacao"]},
        "setor": {"type": "STRING",
                  "enum": ["atendimento", "financeiro", "tecnico", "comercial", "logistica"]},
        "urgencia": {"type": "STRING", "enum": ["baixa", "media", "alta"]},
        "sentimento": {"type": "STRING", "enum": ["positivo", "neutro", "negativo"]},
        "resumo": {"type": "STRING"},
        "palavras_chave": {"type": "ARRAY", "items": {"type": "STRING"}},
        "resposta_sugerida": {"type": "STRING"},
        "confianca": {"type": "NUMBER"},
    },
    "required": ["categoria", "setor", "urgencia", "sentimento", "resumo",
                 "palavras_chave", "resposta_sugerida", "confianca"],
    "propertyOrdering": ["categoria", "setor", "urgencia", "sentimento", "resumo",
                         "palavras_chave", "resposta_sugerida", "confianca"],
}


TENTATIVAS = int(os.getenv("GEMINI_TENTATIVAS", "4"))
ESPERA_BASE = float(os.getenv("GEMINI_ESPERA_BASE", "1.5"))


class ErroIA(Exception):
    """Falha ao obter ou interpretar a resposta da IA."""


def modelo_configurado() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


def extrair_json(texto: str) -> dict:
    """Converte o texto da IA em dict, tolerando blocos ```json ... ```."""
    texto = texto.strip()
    if texto.startswith("```"):
        texto = texto.strip("`")
        if texto.lower().startswith("json"):
            texto = texto[4:]
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fim == -1:
        raise ErroIA("A IA não retornou um objeto JSON.")
    return json.loads(texto[inicio:fim + 1])


def classificar(nome: str, mensagem: str, client: httpx.Client | None = None) -> Classificacao:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ErroIA("GEMINI_API_KEY não configurada.")

    corpo = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": montar_prompt_usuario(nome, mensagem)}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
        },
    }
    http = client or httpx.Client(timeout=60)
    try:
        # Tenta de novo quando o Gemini está sobrecarregado (429/503), com espera crescente
        for tentativa in range(TENTATIVAS):
            resp = http.post(GEMINI_URL.format(model=modelo_configurado()),
                             headers={"x-goog-api-key": api_key}, json=corpo)
            if resp.status_code not in (429, 500, 503) or tentativa == TENTATIVAS - 1:
                break
            time.sleep(ESPERA_BASE * (2 ** tentativa))
    except httpx.HTTPError as exc:
        raise ErroIA(f"Erro de conexão com o Gemini: {exc}") from exc
    finally:
        if client is None:
            http.close()

    if resp.status_code != 200:
        raise ErroIA(f"Gemini respondeu {resp.status_code}: {resp.text[:300]}")

    try:
        texto = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return Classificacao.model_validate(extrair_json(texto))
    except (KeyError, IndexError, json.JSONDecodeError, ValidationError) as exc:
        raise ErroIA(f"Resposta da IA fora do formato esperado: {exc}") from exc
