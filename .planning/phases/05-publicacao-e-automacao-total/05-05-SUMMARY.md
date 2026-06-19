---
phase: 05-publicacao-e-automacao-total
plan: 05-05
subsystem: orchestration
tags: [apscheduler, runner]
requires:
  - phase: 05-04
    provides: publisher
provides:
  - pipeline_runner.run_pipeline_once
  - daemon integrado ao ciclo completo
affects: [n8n]
tech-stack:
  added: []
  patterns: [dependency injection para db e redis]
key-files:
  created:
    - clip-processor/src/pipeline_runner.py
  modified:
    - clip-processor/src/main.py
    - clip-processor/tests/test_pipeline_runner.py
key-decisions:
  - "Falhas em poll ou publish sao logadas e nao derrubam o scheduler."
  - "main.py tem fallback minimo para import local sem apscheduler instalado."
requirements-completed: [ORC-01, PUB-01, PUB-02, PUB-03, PUB-04]
duration: 15min
completed: 2026-06-18
---

# Plan 05-05 Summary

**Pipeline runner integra RSS/AI/renderizacao com publicacao e preserva scheduler resiliente**

## Accomplishments

- `run_pipeline_once()` executa poll/processamento e depois publicacao.
- APScheduler agora agenda `pipeline_cycle`.
- Import de `main.py` permanece seguro em testes.

## Verification

- `pytest tests/test_pipeline_runner.py` passou dentro do run focado.
