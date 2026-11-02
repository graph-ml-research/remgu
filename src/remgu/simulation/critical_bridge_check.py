# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Check reachability after a critical bridge intervention."""
from typing import Mapping
from remgu.simulation.graph_world import GraphWorld
from remgu.simulation.simulation_check import SimulationCheck


class CriticalBridgeCheck(SimulationCheck):
    """Check whether the designated bridge endpoints remain connected."""

    def evaluate(self, world: GraphWorld, labels: Mapping[int, int],
                 predictions: Mapping[int, int]) -> dict[str, object]:
        """Pass when the designated endpoints are disconnected after intervention."""
        del labels, predictions
        bridge = world.critical_bridge
        if bridge is None:
            return {"name": type(self).__name__, "status": "not_evaluated", "details": "No critical bridge is designated"}
        left, right = bridge
        connected = world.reachable(left, right)
        return {"name": type(self).__name__, "status": "failed" if connected else "passed",
                "details": "Bridge endpoints remain connected" if connected else "Bridge endpoints are disconnected",
                "metrics": {"endpoints_connected": connected}}
