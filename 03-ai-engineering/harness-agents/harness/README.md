# Harness na prática

Código do artigo "Harness na prática: 5 peças que tornam o Claude Code confiável no seu projeto .NET".

| Peça | Arquivo |
|---|---|
| CLAUDE.md (índice) | `CLAUDE.md`, `docs/ARCHITECTURE.md` |
| Rules por caminho | `.claude/rules/testes.md` |
| Skill | `.claude/skills/fix-bug/SKILL.md` |
| Teste de arquitetura | `tests/Loja.ArchitectureTests/ArchitectureTests.cs` |
| Hooks | `.claude/settings.json`, `.claude/hooks/*.py` |
| Observabilidade | `.claude/logs/tool-calls.jsonl` (o que o agente fez) e `.claude/logs/decisions.jsonl` (o que o harness decidiu: bloqueios, liberações, desistência) |

## Testar os hooks (sem Claude Code, sem tokens)

    python test_hooks.py

Requer Python 3 e git. No `settings.json`, troque `python` por `python3` ou `py` se for o caso.

## Modos do gate (`verify_done.py`)

- **Padrão:** roda os testes só se algum `.cs` mudou no git (`git status`, restrito à pasta do projeto). Recusa o encerramento até 2 vezes; na 3ª tentativa libera e avisa o humano.
- **`--always`:** roda os testes a cada tentativa de encerrar. Enxerga também o **vermelho herdado**: se o último commit já tem teste falhando e o agente não mudou nada, o modo padrão fica em silêncio. Para ativar, acrescente `"--always"` à lista `args` do hook `Stop` no `settings.json`. O custo é rodar a suíte a cada resposta.


## Observações

- Copie `CLAUDE.md`, `docs/` e `.claude/` para a raiz do seu projeto e adapte nomes (`Loja.*`).
- `ArchitectureTests.cs` assume um projeto xUnit com o pacote `NetArchTest.Rules` e uma classe `Loja.Domain.Pedido`.
  Ajuste o namespace/tipo para o seu domínio. Validado com .NET 10 (`net10.0`) e xUnit v3: o teste passa na base limpa
  e falha quando o `Domain` passa a depender da `Infrastructure`.
- Abra o Claude Code **de dentro desta pasta** (`harness/`), onde está o `.claude/`, e aceite a confiança da pasta;
  abrindo na raiz do repositório, os hooks não são carregados.
- Comando dos testes usado pelo hook Stop: `dotnet test --nologo -v q` (variável `HARNESS_TEST_CMD` sobrescreve).
