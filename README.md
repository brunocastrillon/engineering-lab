🇧🇷 [Ler em português](./README.pt-br.md)

# Engineering Lab

A collection of small, focused engineering experiments exploring software architecture, distributed systems, AI engineering, observability, reliability, failure modes, quantitative experimentation, and technical fragility.

This is not a tutorials repository. Each experiment starts from a real engineering question, states a hypothesis, runs a small controlled test, and documents what the evidence actually showed — the same principle behind my [profile](https://github.com/brunocastrillon):

> Evidence > Assumptions · Experiments > Opinions

## How this lab works

Every experiment lives in its own folder and follows the same structure:

```
Question → Hypothesis → Experiment → Evidence → Conclusion
```

- **Question** — the specific engineering behavior being investigated
- **Hypothesis** — what I expect to happen, and why
- **Experiment** — the minimal setup needed to test it
- **Evidence** — logs, metrics, traces, or benchmark results
- **Conclusion** — what the evidence actually showed, including when the hypothesis was wrong

This repository currently starts as an index of tracks. Individual experiments are added incrementally as they're built.

## Tracks

| # | Track | Focus |
|---|-------|-------|
| 01 | [Software Architecture](./01-software-architecture) | Modular monoliths, boundaries, coupling, dependency inversion |
| 02 | [Distributed Systems](./02-distributed-systems) | Retries, idempotency, eventual consistency, duplicate messages |
| 03 | [AI Engineering](./03-ai-engineering) | RAG, evaluation, agents, hallucination detection, context strategies |
| 04 | [Observability](./04-observability) | Traces, metrics, logs, correlation IDs, OpenTelemetry |
| 05 | [Reliability](./05-reliability) | Retry/backoff, circuit breakers, graceful degradation |
| 06 | [Failure Modes](./06-failure-modes) | Dependency failure, latency injection, partial outages |
| 07 | [Quantitative Experimentation](./07-quantitative-experiments) | Benchmarks, simulations, statistical comparisons |
| 08 | [Technical Fragility](./08-technical-fragility) | Dependency risk, blast radius, SPOFs, fragility scoring |

Most experiments across tracks 01–07 feed into track 08: fragility is what you find once you've stressed a system's architecture, its distributed behavior, its AI components, its observability, its reliability mechanisms, and its failure modes.

## Structure

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

Each track folder holds its own short `README.md` describing its scope. Individual experiments are added as subfolders inside each track as they're built.

## Connect

More context on the ideas behind this lab: [Profile](https://github.com/brunocastrillon).
