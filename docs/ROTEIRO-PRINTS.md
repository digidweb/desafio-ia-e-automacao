# Roteiro de execução e prints

Salve cada print em `docs/prints/` **com o nome exato** abaixo (o README já aponta para eles).

## Preparação (uma vez)
1. Chave Gemini: https://aistudio.google.com/apikey → "Create API key".
2. Dados SMTP da conta de e-mail no cPanel: *E-mail Accounts → Connect Devices* (servidor de saída, porta SSL).
3. `cp .env.example .env` e preencha `GEMINI_API_KEY`, `EMAIL_DESTINO`, `EMAIL_REMETENTE`.
4. `docker compose up -d --build` e abra http://localhost:5678 (crie a conta de dono).
5. Teste rápido da API: abra http://localhost:8000/docs → `POST /classificar` → *Try it out*.
6. n8n: *Import from File* → `n8n/fluxo-classificador.json`.
7. Node *Send Email* → *Credential* → *Create new* (SMTP): host `mail.seudominio.com.br` (ou o servidor
   indicado no cPanel), porta `465`, SSL/TLS ligado, user = e-mail completo, password = senha da conta.
   Se a 465 falhar, tente porta `587` com SSL/TLS desligado (STARTTLS). Salve o fluxo e ative-o.
8. Rode `./exemplos/enviar_exemplos.sh` (ou o `curl` do README).

## Prints
| Arquivo | O que capturar |
|---|---|
| `01-fluxo-completo.png` | Canvas do n8n com os 6 nodes conectados. |
| `02-execucao-sucesso.png` | Aba *Executions* → abra uma execução *Succeeded* (nodes verdes). |
| `03-node-webhook.png` | Node Webhook aberto (método, path, URLs). |
| `04-node-preparar-dados.png` | Node Edit Fields - Preparar dados aberto, com entrada e saída. |
| `05-node-http-request.png` | Node HTTP Request aberto (URL, corpo JSON). |
| `06-node-montar-email.png` | Node Edit Fields - Montar e-mail aberto. |
| `07-node-send-email.png` | Node Send Email aberto (credencial, para, assunto). Cubra seu e-mail se quiser. |
| `08-node-respond.png` | Node Respond to Webhook aberto. |
| `09-resultado-ia.png` | Saída (OUTPUT) do HTTP Request mostrando o JSON da classificação. |
| `10-email-recebido.png` | E-mail na caixa de entrada do destinatário. |
| `11-terminal.png` | Terminal com a saída do `enviar_exemplos.sh`. |

Dica: dentro de uma execução salva (passo 02), clicar em cada node mostra configuração **e** dados juntos.
Assim saem os prints 03 a 09 de uma vez.

## Exportar o fluxo final
Depois de configurado, menu `...` do fluxo → *Download* → substitua `n8n/fluxo-classificador.json`
(confira que não há senha no arquivo; o n8n exporta só o nome da credencial).
