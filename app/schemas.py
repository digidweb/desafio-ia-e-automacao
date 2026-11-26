from enum import Enum

from pydantic import BaseModel, Field


class Categoria(str, Enum):
    duvida = "duvida"
    reclamacao = "reclamacao"
    solicitacao = "solicitacao"


class Setor(str, Enum):
    atendimento = "atendimento"
    financeiro = "financeiro"
    tecnico = "tecnico"
    comercial = "comercial"
    logistica = "logistica"


class Urgencia(str, Enum):
    baixa = "baixa"
    media = "media"
    alta = "alta"


class Sentimento(str, Enum):
    positivo = "positivo"
    neutro = "neutro"
    negativo = "negativo"


class MensagemEntrada(BaseModel):
    nome: str = Field(..., min_length=1, max_length=120, examples=["João Silva"])
    email: str = Field(..., min_length=3, max_length=200, examples=["joao@email.com"])
    mensagem: str = Field(..., min_length=3, max_length=5000,
                          examples=["Meu pedido chegou quebrado e quero meu dinheiro de volta!"])


class Classificacao(BaseModel):
    """Formato que a IA deve devolver (validado antes de sair da API)."""
    categoria: Categoria
    setor: Setor
    urgencia: Urgencia
    sentimento: Sentimento
    resumo: str = Field(..., description="Resumo da mensagem em até 1 frase")
    palavras_chave: list[str] = Field(default_factory=list)
    resposta_sugerida: str = Field(..., description="Rascunho de resposta ao cliente")
    confianca: float = Field(..., ge=0, le=1)


class ClassificacaoResposta(BaseModel):
    cliente: MensagemEntrada
    classificacao: Classificacao
    modelo: str
