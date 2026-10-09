# Harness na prática (parte 3)

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

## Observações

- Copie `CLAUDE.md`, `docs/` e `.claude/` para a raiz do seu projeto e adapte nomes (`Loja.*`).
- `ArchitectureTests.cs` assume um projeto xUnit com o pacote `NetArchTest.Rules` e uma classe `Loja.Domain.Pedido`.
  Ajuste o namespace/tipo para o seu domínio. Validado com .NET 10 (`net10.0`) e xUnit v3: o teste passa na base limpa
  e falha quando o `Domain` passa a depender da `Infrastructure`.
- Abra o Claude Code **de dentro desta pasta** (`harness/`), onde está o `.claude/`, e aceite a confiança da pasta;
  abrindo na raiz do repositório, os hooks não são carregados.
- Comando dos testes usado pelo hook Stop: `dotnet test --nologo -v q` (variável `HARNESS_TEST_CMD` sobrescreve).
