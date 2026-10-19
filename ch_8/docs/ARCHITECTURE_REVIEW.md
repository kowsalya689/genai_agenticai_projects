# Architecture Review

*Acting as a Senior Software Architect reviewing the generated application.*

## Framework choice: FastAPI vs Flask

**FastAPI is the better fit for this project**, for four concrete reasons:

1. **Validation is a requirement.** The brief calls for input validation.
   FastAPI + Pydantic gives declarative, automatic request validation (empty
   text, `top_k`/`num_words`/`temperature` bounds) with structured `422`
   errors — in Flask this is hand-rolled per route.
2. **Self-documenting API.** OpenAPI/Swagger UI at `/docs` is generated from
   the schemas for free, which matters for an API meant to be consumed.
3. **Concurrency.** ASGI + async lets the server handle concurrent requests
   without a heavier WSGI worker setup; model inference can be offloaded
   without rearchitecting.
4. **Typing.** Typed request/response models make the contract explicit and
   refactors safer.

Flask remains a fine choice for a minimal demo, and because the
service/model/utils layers are framework-agnostic, a Flask port only touches
the routing layer.

## Evaluation

| Dimension | Assessment | Notes |
|---|---|---|
| **Scalability** | Good for stateless horizontal scaling | Model loaded once per process (cached singleton); scale by running N workers/replicas behind a load balancer. |
| **Maintainability** | Strong | Clear separation: `utils` (preprocessing) / `services` (inference) / `models` (loading + schemas) / `routes` (HTTP). Framework-agnostic core. |
| **Code quality** | Strong | Type hints, docstrings, single-responsibility modules, dependency injection for the predictor (easy to mock). |
| **API design** | Strong | REST verbs, typed schemas, bounded inputs, `/health` for probes, OpenAPI docs. |
| **Deployment readiness** | Good | Dockerfile + Render/Railway configs, `$PORT` aware, env-var-configurable paths, graceful startup if artifacts missing. |
| **Production suitability** | Solid MVP | Sensible defaults; a few hardening items below before heavy production use. |

## Recommended improvements (prioritised)

**High impact**
1. **Concurrency safety for inference.** A single Keras model instance under an
   async server can serialize/contend on prediction. Wrap `model.predict` in a
   thread pool (`run_in_threadpool`) or a dedicated inference worker/queue, and
   consider batching.
2. **Model serving at scale.** For real load, serve the model via **TensorFlow
   Serving** or **ONNX Runtime** and keep FastAPI as a thin gateway — decouples
   API scaling from model memory.
3. **Structured logging + metrics.** Add request logging, latency/throughput
   metrics (Prometheus), and error tracking (Sentry).

**Medium impact**
4. **Rate limiting & payload caps** (e.g. `slowapi`) to protect the inference
   path from abuse; cap input length explicitly.
5. **Caching** identical `(text, top_k)` predictions (LRU / Redis) to cut
   repeat compute.
6. **Config via `pydantic-settings`** with typed env parsing and a `.env`
   file, replacing the hand-rolled settings class.
7. **CORS policy** if the UI and API are served from different origins.

**Lower impact / hygiene**
8. **CI pipeline** (lint + `pytest` on push), pre-commit (ruff/black).
9. **Artifact versioning** — record model version/hash in `/health` and logs
   for traceability.
10. **Security headers** and running behind a production ASGI server config
    (Gunicorn + Uvicorn workers) with sensible timeouts.

## Summary

The application is a clean, modular, well-tested MVP that faithfully preserves
the notebook's preprocessing and prediction logic while exposing it through a
typed REST API and UI. The core is production-*shaped*; the main work before
heavy production traffic is inference concurrency/serving, observability, and
abuse protection.
