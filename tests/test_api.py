import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app import gemini
from app.main import app

RESPOSTA_IA = {
    "categoria": "reclamacao", "setor": "logistica", "urgencia": "alta",
    "sentimento": "negativo", "resumo": "Pedido chegou quebrado.",
    "palavras_chave": ["pedido", "quebrado"],
    "resposta_sugerida": "Olá, João! Sentimos muito.", "confianca": 0.93,
}


def resposta_gemini(texto: str) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": texto}]}}]}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "teste")
    return TestClient(app)


def mock_gemini(monkeypatch, status=200, payload=None):
    def handler(request: httpx.Request):
        corpo = json.loads(request.content)
        assert corpo["generationConfig"]["responseMimeType"] == "application/json"
        assert request.headers["x-goog-api-key"] == "teste"
        return httpx.Response(status, json=payload)

    original = gemini.classificar
    monkeypatch.setattr(gemini, "classificar", lambda n, m: original(
        n, m, client=httpx.Client(transport=httpx.MockTransport(handler))))


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_classifica_mensagem(client, monkeypatch):
    mock_gemini(monkeypatch, payload=resposta_gemini(json.dumps(RESPOSTA_IA)))
    r = client.post("/classificar", json={"nome": "João", "email": "j@x.com",
                                          "mensagem": "Meu pedido chegou quebrado!"})
    assert r.status_code == 200
    dados = r.json()
    assert dados["classificacao"]["categoria"] == "reclamacao"
    assert dados["cliente"]["nome"] == "João"


def test_aceita_json_em_bloco_markdown(client, monkeypatch):
    texto = "```json\n" + json.dumps(RESPOSTA_IA) + "\n```"
    mock_gemini(monkeypatch, payload=resposta_gemini(texto))
    r = client.post("/classificar", json={"nome": "A", "email": "a@x.com", "mensagem": "abc"})
    assert r.status_code == 200


def test_categoria_invalida_vira_502(client, monkeypatch):
    invalido = dict(RESPOSTA_IA, categoria="elogio")
    mock_gemini(monkeypatch, payload=resposta_gemini(json.dumps(invalido)))
    r = client.post("/classificar", json={"nome": "A", "email": "a@x.com", "mensagem": "abc"})
    assert r.status_code == 502


def test_erro_do_gemini_vira_502(client, monkeypatch):
    monkeypatch.setattr(gemini, "ESPERA_BASE", 0)
    mock_gemini(monkeypatch, status=429, payload={"error": "quota"})
    r = client.post("/classificar", json={"nome": "A", "email": "a@x.com", "mensagem": "abc"})
    assert r.status_code == 502


def test_validacao_de_entrada(client):
    r = client.post("/classificar", json={"nome": "A", "email": "a@x.com", "mensagem": ""})
    assert r.status_code == 422


def test_sem_chave_vira_502(client, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY")
    r = client.post("/classificar", json={"nome": "A", "email": "a@x.com", "mensagem": "abc"})
    assert r.status_code == 502


def test_tenta_de_novo_quando_gemini_sobrecarregado(client, monkeypatch):
    monkeypatch.setattr(gemini, "ESPERA_BASE", 0)
    chamadas = {"n": 0}

    def handler(request):
        chamadas["n"] += 1
        if chamadas["n"] < 3:
            return httpx.Response(503, json={"error": "high demand"})
        return httpx.Response(200, json=resposta_gemini(json.dumps(RESPOSTA_IA)))

    original = gemini.classificar
    monkeypatch.setattr(gemini, "classificar", lambda n, m: original(
        n, m, client=httpx.Client(transport=httpx.MockTransport(handler))))
    r = client.post("/classificar", json={"nome": "A", "email": "a@x.com", "mensagem": "abc"})
    assert r.status_code == 200
    assert chamadas["n"] == 3
