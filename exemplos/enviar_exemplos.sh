#!/usr/bin/env bash
# Envia as mensagens de exemplo para o webhook do n8n.
# Uso: ./exemplos/enviar_exemplos.sh [URL_DO_WEBHOOK]
URL="${1:-http://localhost:5678/webhook/mensagens}"
python3 - "$URL" <<'PY'
import json, sys, urllib.error, urllib.request
url = sys.argv[1]
for msg in json.load(open("exemplos/mensagens.json", encoding="utf-8")):
    req = urllib.request.Request(url, data=json.dumps(msg).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=90)
    except urllib.error.HTTPError as e:
        print(f"{msg['nome']:<15} -> ERRO {e.code}: {e.read().decode(errors='ignore')[:300]}")
        if e.code == 404:
            print("Dica: o fluxo não está ativo/publicado no n8n (ou use a URL /webhook-test/ após clicar em 'Execute workflow').")
            sys.exit(1)
        continue
    with r:
        dados = json.load(r)
        c = dados.get("classificacao", dados)
        print(f"{msg['nome']:<15} -> {c.get('categoria')} / {c.get('setor')} / {c.get('urgencia')}")
PY
