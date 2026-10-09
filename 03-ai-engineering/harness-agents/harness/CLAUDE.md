# Loja API

ASP.NET Core · EF Core · xUnit. Camadas: Domain → Application → Infrastructure → Api.

## Comandos
- Build: `dotnet build`
- Testes: `dotnet test` (inclui testes de arquitetura; nunca ignore falhas)

## Onde está o quê (leia sob demanda)
- Regras de dependência entre camadas: docs/ARCHITECTURE.md
- Convenções de teste: carregadas automaticamente em tests/ (.claude/rules)

## Inegociáveis
- Nunca edite `Migrations/` à mão: use `dotnet ef migrations add`.
- Bug reportado? Use a skill `/fix-bug`.
