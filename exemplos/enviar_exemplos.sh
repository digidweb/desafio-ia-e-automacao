#!/usr/bin/env bash
# Envia as mensagens de exemplo para o webhook do n8n.
# Uso: ./exemplos/enviar_exemplos.sh [URL_DO_WEBHOOK]
URL="${1:-http://localhost:5678/webhook/mensagens}"
python3 - "$URL" <<'PY'
import json, sys, urllib.request
url = sys.argv[1]
for msg in json.load(open("exemplos/mensagens.json", encoding="utf-8")):
    req = urllib.request.Request(url, data=json.dumps(msg).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        dados = json.load(r)
        c = dados.get("classificacao", dados)
        print(f"{msg['nome']:<15} -> {c.get('categoria')} / {c.get('setor')} / {c.get('urgencia')}")
PY
