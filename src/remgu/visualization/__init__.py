# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Optional dependency-free visualization and reporting tools."""
from remgu.visualization.architecture_adapter import ArchitectureAdapter, ModelAdapter
from remgu.visualization.dot_svg_renderer import DotSvgRenderer
from remgu.visualization.graph_renderer import GraphRenderer
from remgu.visualization.image_renderer import ImageRenderer
from remgu.visualization.metric_renderer import MetricRenderer
from remgu.visualization.resource_monitor import ResourceMonitor
from remgu.visualization.static_html_report import StaticHtmlReport
from remgu.visualization.table_renderer import TableRenderer
from remgu.visualization.text_renderer import TextRenderer
__all__ = ["ArchitectureAdapter", "ModelAdapter", "DotSvgRenderer", "GraphRenderer", "ImageRenderer", "MetricRenderer", "ResourceMonitor", "StaticHtmlReport", "TableRenderer", "TextRenderer"]
from remgu.visualization.embedding_renderer import EmbeddingRenderer
__all__ += ["EmbeddingRenderer"]
from remgu.visualization.catboost_architecture_adapter import CatBoostArchitectureAdapter
from remgu.visualization.keras_architecture_adapter import KerasArchitectureAdapter
from remgu.visualization.spacy_architecture_adapter import SpacyPipelineArchitectureAdapter
from remgu.visualization.torch_architecture_adapter import TorchArchitectureAdapter
from remgu.visualization.word2vec_architecture_adapter import Word2VecArchitectureAdapter
__all__ += ["CatBoostArchitectureAdapter", "KerasArchitectureAdapter", "SpacyPipelineArchitectureAdapter", "TorchArchitectureAdapter", "Word2VecArchitectureAdapter"]
