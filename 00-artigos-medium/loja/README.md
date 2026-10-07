# Harness na prática

Código do artigo "Harness na prática: 5 peças que tornam o Claude Code confiável no seu projeto .NET".

| Peça | Arquivo |
|---|---|
| CLAUDE.md (índice) | `CLAUDE.md`, `docs/ARCHITECTURE.md` |
| Rules por caminho | `.claude/rules/testes.md` |
| Skill | `.claude/skills/fix-bug/SKILL.md` |
| Teste de arquitetura | `tests/Loja.ArchitectureTests/ArchitectureTests.cs` |
| Hooks | `.claude/settings.json`, `.claude/hooks/*.py` |

## Testar os hooks (sem Claude Code, sem tokens)

    python test_hooks.py

Requer Python 3 e git. No `settings.json`, troque `python` por `python3` ou `py` se for o caso.

## Observações

- Copie `CLAUDE.md`, `docs/` e `.claude/` para a raiz do seu projeto e adapte nomes (`Loja.*`).
- `ArchitectureTests.cs` assume um projeto xUnit com o pacote `NetArchTest.Rules` e uma classe `Loja.Domain.Pedido`.
  Ajuste o namespace/tipo para o seu domínio. Este arquivo é ilustrativo.
- Comando dos testes usado pelo hook Stop: `dotnet test --nologo -v q` (variável `HARNESS_TEST_CMD` sobrescreve).
