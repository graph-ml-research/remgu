# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
from .experiment import Experiment
from .models import Motivation
from .run import Run



__all__ = ["Experiment", "Motivation", "Run"]


from remgu.example.example_provider import ExampleProvider
from remgu.example.example_selector import ExampleSelector, TopKSelector

__all__ += ["ExampleProvider", "ExampleSelector", "TopKSelector"]

from .research_snapshot import ResearchSnapshot, ResearchSnapshotBuilder
from .consistency import ResearchChecker, ConsistencyIssue, ConsistencyReport
from .publication import ArchiveAdapter, MarkdownAdapter, StaticSiteAdapter

__all__ += ["ResearchSnapshot", "ResearchSnapshotBuilder", "ResearchChecker", "ConsistencyIssue", "ConsistencyReport", "ArchiveAdapter", "MarkdownAdapter", "StaticSiteAdapter"]

from remgu.simulation import (
    AddIsolatedNodesOperator,
    CriticalBridgeCheck,
    GraphDependencyTask,
    GraphOperator,
    GraphReachabilityBaseline,
    GraphWorld,
    GraphWorldGenerator,
    PredictionAccuracyCheck,
    RandomSource,
    RemoveEdgeOperator,
    ResearchRunAdapter,
    SimulationCheck,
    SimulationConfig,
    SimulationExperiment,
    SimulationResult,
    SimulationRunner,
    Transform,
    NumericNoiseTransform,
    TransformPipeline,
    Probe,
    ModelIntervener,
)

__all__ += [
    "AddIsolatedNodesOperator", "CriticalBridgeCheck", "GraphDependencyTask", "GraphOperator",
    "GraphReachabilityBaseline", "GraphWorld", "GraphWorldGenerator", "PredictionAccuracyCheck",
    "RandomSource", "RemoveEdgeOperator", "ResearchRunAdapter", "SimulationCheck", "SimulationConfig",
    "SimulationExperiment", "SimulationResult", "SimulationRunner", "Transform", "NumericNoiseTransform",
    "TransformPipeline", "Probe", "ModelIntervener",
]

from remgu.visualization import (
    ArchitectureAdapter, ModelAdapter, Renderer, DotSvgRenderer, GraphRenderer, ImageRenderer,
    MetricRenderer, ResourceMonitor, StaticHtmlReport, TableRenderer, TextRenderer,
)
from remgu.dashboard import DashboardServer, ExperimentController

__all__ += [
    "ArchitectureAdapter", "ModelAdapter", "Renderer", "DotSvgRenderer", "GraphRenderer", "ImageRenderer",
    "MetricRenderer", "ResourceMonitor", "StaticHtmlReport", "TableRenderer", "TextRenderer",
    "DashboardServer", "ExperimentController",
]
from remgu.example import ExampleSelectionService, ExampleReportSelector, SyntheticExampleGenerator
from remgu.visualization import EmbeddingRenderer
__all__ += ["ExampleSelectionService", "ExampleReportSelector", "SyntheticExampleGenerator", "EmbeddingRenderer"]
from remgu.visualization import (
    CatBoostArchitectureAdapter, KerasArchitectureAdapter,
    SpacyPipelineArchitectureAdapter, TorchArchitectureAdapter, Word2VecArchitectureAdapter,
)
__all__ += ["CatBoostArchitectureAdapter", "KerasArchitectureAdapter", "SpacyPipelineArchitectureAdapter", "TorchArchitectureAdapter", "Word2VecArchitectureAdapter"]
