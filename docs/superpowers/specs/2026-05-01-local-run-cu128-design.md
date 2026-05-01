---
feature: local-run-cu128
doc_type: spec
tags: [cuda, cu128, torch, embedders, semantic-search, local-dev]
---

# Local-run CUDA 12.8 (cu128) support

**Branch**: `feature/local-run` (forked from `feature/postgres-weaviate`)
**Date**: 2026-05-01
**Status**: Approved (pending implementation)

## Goal

Let developers run the FastAPI backend locally on machines that need CUDA 12.8 wheels (Blackwell-generation GPUs: RTX 50-series, H100/B100). Today the Makefile only ships `install-ml-cpu` and `install-ml-gpu` (cu124). cu128 wheels do not exist for the currently-pinned `torch==2.6.0`, so this design bumps PyTorch to 2.7.1 and replaces the GPU install matrix with explicit per-CUDA targets.

## Why now

User reports that starting the backend on their local machine does not pick up GPU acceleration, and their hardware needs cu128. cu128 is required for sm_120 (Blackwell). The default cu124 wheel will not run on these GPUs even at lower precision.

## Non-goals

- No code changes to embedder modules (`bge.py`, `fgclip.py`) or `search_service.py`.
- No model substitution — keep `BAAI/bge-small-en-v1.5` and `qihoo360/fg-clip2-base`.
- No fp16/bf16 toggle. Defer until there is a measured need.
- No Docker / container packaging changes.
- No CI changes — local dev only.

## Design

### 1. Pin bumps in `backend/requirements-ml.txt`

| Package | Old | New |
|---|---|---|
| `torch` | `2.6.0` | `2.7.1` |
| `torchvision` | `0.21.0` | `0.22.1` |

Other ML pins are unchanged: `transformers>=4.56,<5`, `sentence-transformers>=3.3.1,<5`, `huggingface-hub>=0.34.0,<1`, `pillow==10.4.0`, `numpy==1.26.4`, `einops==0.8.0`, `weaviate-client>=4.9,<5`, `cachetools==5.5.0`, `redis==5.2.0`. All are compatible with torch 2.7.

### 2. Makefile install matrix

Replace the existing 2 targets (`install-ml-cpu`, `install-ml-gpu`) with 3 explicit targets. Drop the `install-ml-gpu` alias (YAGNI).

| Target | Index URL | Wheel suffix | Use for |
|---|---|---|---|
| `install-ml-cpu` | `https://download.pytorch.org/whl/cpu` | `+cpu` | No GPU, fallback for CI / smoke |
| `install-ml-cu126` | `https://download.pytorch.org/whl/cu126` | `+cu126` | RTX 30/40, A100, V100, T4 (replaces previous cu124 target — torch 2.7 dropped cu124) |
| `install-ml-cu128` | `https://download.pytorch.org/whl/cu128` | `+cu128` | RTX 50-series, H100, B100 (requires sm_90+) |

All three install `torch==2.7.1+<suffix> torchvision==0.22.1+<suffix>` then `pip install -r backend/requirements-ml.txt` to layer the rest.

`.PHONY` line and `help:` text updated. `check-ml-env`, `reindex*` targets unchanged.

### 3. `scripts/check_ml_env.py` diagnostics

Add a short device report at the top of the script's output, before the existing BGE smoke load:

```
torch                : 2.7.1
torch.version.cuda   : 12.8
torch.cuda.is_available: True
device count         : 1
device 0             : NVIDIA GeForce RTX 5090 (sm_120)
```

If `torch.cuda.is_available()` is `False`, print the same lines with `cuda: None` and a hint that the user is on the cpu wheel. No new dependency.

### 4. Docs

- `Makefile` `help` block — replace the two old GPU lines with three new ones.
- `CLAUDE.md` — search for any `install-ml-gpu` reference and update.
- `README.md` — same.
- No change to `docs/features/...` (those describe runtime semantics, not install).
- No change to `.env.example` (`SEMANTIC_DEVICE` values unchanged).

### 5. Code that does NOT change

- `backend/app/services/search/embedders/bge.py` — `_resolve_device()` reads `SEMANTIC_DEVICE` and falls back to `cuda` if available. Agnostic to cu version.
- `backend/app/services/search/embedders/fgclip.py` — same dynamic device resolution.
- `backend/app/services/search/search_service.py` — orchestrator only; no torch calls.
- `backend/app/main.py` — lifespan preload (added in prior task) works as-is on torch 2.7.

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| `sentence-transformers` 3.3.x has a hidden incompatibility with torch 2.7 | Allowed range `>=3.3.1,<5` already covers 4.x; bump if encode fails. |
| `transformers` `AutoModelForCausalLM.from_pretrained(... walk_type="short")` no longer accepted | walk_type is FG-CLIP-specific and forwarded by `trust_remote_code` model code; unaffected by transformers core version. |
| Existing developers had `install-ml-gpu` muscle memory | `Makefile help` lists new targets; one-time friction. |
| torchvision 0.22.1 changed the default `read_image` mode | We do not call torchvision IO; embedders use PIL directly. |
| Numpy 1.26 vs torch 2.7 | torch 2.7 still supports numpy 1.26.x (numpy 2.x is also supported but we keep 1.26 for stability). |

## Verification plan

After implementation, on the user's local machine:

1. `make install-ml-cu128` — clean install into the existing venv (or a fresh one).
2. `make check-ml-env` — must print `torch.version.cuda: 12.8` and the GPU name.
3. `make run-backend` — startup log must show `Embedders ready in <X>s` (lifespan preload from prior task).
4. Issue a `/products/search?q=...` request — first call latency comparable to subsequent calls.

## Out of scope / follow-ups

- Adding a `make install-ml-cu118` for older Pascal/Maxwell — nobody asked.
- Switching FG-CLIP to a quantized variant for VRAM savings.
- Auto-selecting cu126 vs cu128 based on detected GPU — would couple Makefile to runtime detection; keep manual.
