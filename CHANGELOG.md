# Changelog

## [1.1.0] - 2026-10-09

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-08

### Added
- Local TF-IDF support ticket intent classification engine with n-gram tokenization and calibrated multi-class probability scoring.
- Comprehensive model evaluation pipeline computing confusion matrices, per-class precision/recall/F1, and discriminative n-gram feature weights.
- Automated triage pipeline with confidence and margin thresholding to route ambiguous tickets into a human-in-the-loop review queue.
- Human review queue interface for inspecting candidate predictions, assigning ground truth, and exporting fine-tuning feedback.
- Opt-in LLM advisory service supporting OpenAI-compatible, Anthropic, Gemini, and Ollama providers with local offline fallback.
- OIDC authorization-code integration with Keycloak (PKCE, state, nonce) and local demo mode with role-based access control (viewer, operator, admin).
- Fast, typed React + TypeScript + Vite frontend with interactive confusion matrix visualization, triage workbench, and dataset manager.
- SQLite transactional persistence with parameterized queries, audit logging, and pagination.
- Docker multi-stage containers with non-root execution and Compose orchestration.
