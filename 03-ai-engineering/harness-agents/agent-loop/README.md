# Agent loop na prática (parte 4)

Código do artigo "Agent loop na prática: construindo um agente de código do zero em Python".

## Rodar de verdade

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1               # macOS/Linux: source .venv/bin/activate
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY="sk-ant-..."     # PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-..."
    python agent.py "Faça o pytest passar."

A chave precisa ser uma **variável de ambiente**: um arquivo `.env` não é lido automaticamente. A API é cobrada à parte
do plano do claude.ai. No Windows PowerShell 5.1, leia os logs com `Get-Content ... -Encoding UTF8`.

O agente edita `workspace/calc.py` (que começa com um bug). Para repetir, restaure o bug:
`return sum(valores) / (len(valores) - 1)`. Rastros em `traces/`, episódios em `memory/`.

## Rodar sem chave (API simulada)

    python simulate_agent.py

Executa 8 cenários com o SDK oficial contra uma API falsa: caminho feliz, guardrail de comando,
guardrail de caminho, "terminei" prematuro, repetição sem progresso, orçamento de passos, decodificação de saída e timeout da verificação.
Isso valida o loop e os guardrails, mas NÃO substitui uma execução real com o modelo.

## Aviso de segurança

`safe_path` e a allowlist não são um sandbox: `pytest` executa o código do projeto.
Em produção, rode dentro de um container sem rede e sem credenciais.
