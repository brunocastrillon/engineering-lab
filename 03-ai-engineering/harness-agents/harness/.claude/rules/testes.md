---
paths:
  - "tests/**/*.cs"
---
# Convenções de teste
- Nome: `Metodo_Cenario_ResultadoEsperado`.
- Um `Assert` lógico por teste. Sem lógica condicional dentro do teste.
- Dados de teste via builders em `tests/Loja.Tests/Builders`, nunca JSON solto.
