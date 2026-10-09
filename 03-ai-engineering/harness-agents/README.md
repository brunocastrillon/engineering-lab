# Série Harness e Agents: código dos artigos

Código que acompanha a série de artigos no Medium sobre a engenharia por trás da IA que funciona de verdade, para desenvolvedores intermediários e sêniores.

| Parte | Artigo | Tipo | Código |
|---|---|---|---|
| 1 | [Harness: por que o modelo é só 20% do resultado do seu agente de IA](https://medium.com/@brunocastrillon/harness-por-que-o-modelo-%C3%A9-s%C3%B3-20-do-resultado-do-seu-agente-de-ia-74ba75bc2cd8) | Teoria | — |
| 2 | [Agents: a diferença entre um modelo que responde e um sistema que age](https://medium.com/@brunocastrillon/agents-a-diferen%C3%A7a-entre-um-modelo-que-responde-e-um-sistema-que-age-faef0a9ec427) | Teoria | — |
| 3 | Harness na prática: 5 peças que tornam o Claude Code confiável no seu projeto .NET — [LINK DA PARTE 3] | Prática | [`loja/`](./loja) |
| 4 | Agent loop na prática: construindo um agente de código do zero em Python — [LINK DA PARTE 4] | Prática | [`agent-loop/`](./agent-loop) |

## Estrutura

```
00-artigos-medium/
├── loja/          # parte 3: harness do Claude Code em um projeto .NET
└── agent-loop/    # parte 4: agent loop em Python, do zero
```

## Parte 3: `loja/`

Uma API .NET em camadas (`Loja.Domain`, `Loja.Infrastructure`) com as cinco peças do harness: `CLAUDE.md`, rules, skill, teste de arquitetura e hooks (`.claude/`).

```powershell
cd loja
python test_hooks.py     # 30 verificações dos hooks; não usa o modelo nem gasta tokens
dotnet test              # testes de domínio e de arquitetura
```

Para ver os hooks em ação, abra o Claude Code **de dentro da pasta `loja`** (é onde está o `.claude/`) e aceite a confiança da pasta. Os dois diários ficam em `loja/.claude/logs/` (`tool-calls.jsonl` e `decisions.jsonl`) e não vão para o git.

## Parte 4: `agent-loop/`

Um agente de manutenção de código em um arquivo (`agent.py`): tools, guardrails, critérios de parada, verificação independente, memória e observabilidade.

```powershell
cd agent-loop
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python simulate_agent.py                      # 8 cenários contra uma API simulada; sem chave, sem custo
$env:ANTHROPIC_API_KEY = "sk-ant-..."         # chave com crédito (a API é cobrada à parte do claude.ai)
python agent.py "Faça o pytest passar."       # execução real
```

O `workspace/calc.py` começa com um bug de propósito. Para repetir um experimento: `git restore workspace/calc.py`. Rastros em `traces/` e episódios em `memory/` (ambos fora do git). No Windows PowerShell 5.1, leia os logs com `Get-Content ... -Encoding UTF8`.

## Testado com

- Windows, PowerShell e Claude Code
- .NET 10 (`net10.0`) e xUnit v3
- Python [VERSÃO DO PYTHON], SDK `anthropic` [VERSÃO DO SDK] e o modelo `claude-sonnet-5-5`

## Avisos

- **Nada aqui é um sandbox.** O guard dos hooks e o `safe_path` do agente reduzem acidentes, mas não isolam. Em produção, rode o agente em um contêiner sem rede e sem credenciais.
- **Nunca commite chaves.** Se usar um `.env`, confirme com `git check-ignore -v .env` que ele está ignorado.
