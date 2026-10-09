---
name: fix-bug
description: Corrige bugs reproduzindo primeiro com um teste que falha. Use quando o usuário relatar um bug, erro ou comportamento inesperado.
---
# Procedimento
1. Reproduza: escreva um teste xUnit que falha e prove o bug (`dotnet test --filter`).
2. Ache a causa raiz. Não corrija o sintoma.
3. Corrija com a menor mudança possível, respeitando docs/ARCHITECTURE.md.
4. Rode `dotnet test` completo, incluindo os testes de arquitetura.
5. Reporte: causa raiz, arquivos alterados, teste que cobre o bug.
