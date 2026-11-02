# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Optional conceptual architecture view for Word2Vec-style embedding models."""


class Word2VecArchitectureAdapter:
    """Show the embedding lookup flow without pretending Word2Vec is a layer stack."""

    def get_architecture_dot(self, model: object) -> str | None:
        """Return a conceptual DOT view when vector size can be determined."""
        keyed_vectors = getattr(model, "wv", None)
        vector_size = getattr(keyed_vectors, "vector_size", None) if keyed_vectors is not None else getattr(model, "vector_size", None)
        if vector_size is None: return None
        return ("digraph Word2Vec {\n"
                '  token [label="Input token/context"];\n'
                '  lookup [label="Embedding lookup"];\n'
                f'  vector [label="Vector: {int(vector_size)} dimensions"];\n'
                "  token -> lookup -> vector;\n}")
