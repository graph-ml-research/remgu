# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Tests for the common simulation-world contract."""
import unittest

from remgu import GraphWorld, SimulationWorld, WorldRenderer


class TestSimulationWorld(unittest.TestCase):
    """Check that GraphWorld implements the generic world interface."""

    def test_graph_world_implements_shared_contract(self):
        world = GraphWorld({0: {1}, 1: {0}}, {0: 0.0, 1: 1.0}, {0: 0, 1: 1}, (0, 1))
        self.assertIsInstance(world, SimulationWorld)
        self.assertIn("2 nodes", world.summary())
        self.assertEqual(world.to_ascii(), world.to_text())
        self.assertEqual(world.to_dict()["critical_bridge"], [0, 1])

    def test_generic_renderer_works_without_graph_specific_api(self):
        world = GraphWorld({0: set()}, {0: 1.0}, {0: 0})
        rendered = WorldRenderer().render(world)
        self.assertIn("GraphWorld", rendered)
        self.assertIn("Nodes:", rendered)

    def test_generic_renderer_rejects_non_world_data(self):
        with self.assertRaises(TypeError):
            WorldRenderer().render({"text": "not a world"})
