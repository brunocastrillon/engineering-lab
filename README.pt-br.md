🇺🇸 [Read in English](./README.md)

# Laboratório de Engenharia

Uma coleção de experimentos de engenharia pequenos e focados, explorando arquitetura de software, sistemas distribuídos, engenharia de IA, observabilidade, confiabilidade, modos de falha, experimentação quantitativa e fragilidade técnica.

Isto não é um repositório de tutoriais. Cada experimento parte de uma pergunta de engenharia real, declara uma hipótese, executa um teste controlado pequeno e documenta o que a evidência realmente mostrou — o mesmo princípio por trás do meu [perfil](https://github.com/brunocastrillon):

> Evidência > Suposições · Experimentos > Opiniões

## Como este laboratório funciona

Cada experimento vive na sua própria pasta e segue a mesma estrutura:

```
Pergunta → Hipótese → Experimento → Evidência → Conclusão
```

- **Pergunta** — o comportamento de engenharia específico sendo investigado
- **Hipótese** — o que eu espero que aconteça, e por quê
- **Experimento** — a configuração mínima necessária para testá-la
- **Evidência** — logs, métricas, traces ou resultados de benchmark
- **Conclusão** — o que a evidência realmente mostrou, incluindo quando a hipótese estava errada

Este repositório começa como um índice de trilhas. Experimentos individuais são adicionados de forma incremental à medida que são construídos.

## Trilhas

| # | Trilha | Foco |
|---|-------|-------|
| 01 | [Arquitetura de Software](./01-software-architecture) | Monólitos modulares, fronteiras, acoplamento, inversão de dependência |
| 02 | [Sistemas Distribuídos](./02-distributed-systems) | Retries, idempotência, consistência eventual, mensagens duplicadas |
| 03 | [Engenharia de IA](./03-ai-engineering) | RAG, avaliação, agentes, detecção de alucinação, estratégias de contexto |
| 04 | [Observabilidade](./04-observability) | Traces, métricas, logs, correlation IDs, OpenTelemetry |
| 05 | [Confiabilidade](./05-reliability) | Retry/backoff, circuit breakers, degradação graciosa |
| 06 | [Modos de Falha](./06-failure-modes) | Falha de dependência, injeção de latência, indisponibilidades parciais |
| 07 | [Experimentação Quantitativa](./07-quantitative-experiments) | Benchmarks, simulações, comparações estatísticas |
| 08 | [Fragilidade Técnica](./08-technical-fragility) | Risco de dependência, blast radius, SPOFs, pontuação de fragilidade |

A maioria dos experimentos das trilhas 01–07 converge para a trilha 08: fragilidade é o que se encontra depois de estressar a arquitetura de um sistema, seu comportamento distribuído, seus componentes de IA, sua observabilidade, seus mecanismos de confiabilidade e seus modos de falha.

## Estrutura

```
engineering-lab/
├── README.md
├── 01-software-architecture/
├── 02-distributed-systems/
├── 03-ai-engineering/
├── 04-observability/
├── 05-reliability/
├── 06-failure-modes/
├── 07-quantitative-experiments/
└── 08-technical-fragility/
```

Cada pasta de trilha tem seu próprio `README.md` curto descrevendo seu escopo. Experimentos individuais são adicionados como subpastas dentro de cada trilha à medida que são construídos.

## Conecte-se

Mais contexto sobre as ideias por trás deste laboratório: [Perfil](https://github.com/brunocastrillon).
