"""Smoke test the semantic-search ML stack.

Loads the BGE encoder and runs one forward pass to detect dependency
issues before reindexing or serving. Does not load FG-CLIP 2 (weights
heavy); a separate `--full` flag would be added in the future.
"""

import os
import sys

# Resolve backend imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def main() -> int:
    import numpy as np
    import torch
    import transformers
    import sentence_transformers
    import weaviate

    print(f"python      = {sys.version.split()[0]}")
    print(f"torch       = {torch.__version__}, cuda={torch.cuda.is_available()}")
    print(f"transformers= {transformers.__version__}")
    print(f"sentence_t. = {sentence_transformers.__version__}")
    print(f"weaviate    = {weaviate.__version__}")
    print(f"numpy       = {np.__version__}")

    from sentence_transformers import SentenceTransformer

    model_id = os.environ.get("SEMANTIC_TEXT_MODEL", "BAAI/bge-small-en-v1.5")
    m = SentenceTransformer(model_id)
    v = m.encode(["hello world"])
    assert v.shape == (1, 384), f"unexpected shape {v.shape}"
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
