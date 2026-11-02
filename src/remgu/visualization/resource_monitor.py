# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Optional best-effort process and device resource sampling."""
from __future__ import annotations
import time


class ResourceMonitor:
    """Sample available CPU/RAM/GPU metrics and retain observed peaks.

    Optional ``psutil`` and ``pynvml`` integrations are discovered lazily.
    Missing measurements are represented by ``None`` rather than zero. This
    class never shells out to a GPU utility or imports ML frameworks.
    """

    def __init__(self) -> None:
        """Initialize sampling state without importing optional dependencies."""
        self.started_at = time.perf_counter()
        self._peak_ram_bytes = None
        self._peak_vram_bytes = None
        self._last_snapshot = {}

    def sample(self) -> dict[str, int | float | None]:
        """Return one best-effort live snapshot and update observed peaks."""
        snapshot = {"timestamp_seconds": time.perf_counter() - self.started_at,
                    "cpu_percent_process": None, "ram_bytes_process": None,
                    "ram_bytes_system_used": None, "vram_bytes_device_used": None,
                    "gpu_utilization_percent": None}
        try:
            import psutil
            process = psutil.Process()
            snapshot["cpu_percent_process"] = process.cpu_percent(interval=None)
            snapshot["ram_bytes_process"] = process.memory_info().rss
            self._peak_ram_bytes = max(self._peak_ram_bytes or 0, int(snapshot["ram_bytes_process"]))
            memory = psutil.virtual_memory()
            snapshot["ram_bytes_system_used"] = memory.total - memory.available
        except Exception:
            pass
        try:
            import pynvml
            if not getattr(self, "_nvml_initialized", False):
                pynvml.nvmlInit()
                self._nvml_initialized = True
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                snapshot["vram_bytes_device_used"] = int(memory_info.used)
                snapshot["gpu_utilization_percent"] = float(utilization.gpu)
                self._peak_vram_bytes = max(self._peak_vram_bytes or 0, int(memory_info.used))
        except Exception:
            pass
        snapshot["peak_ram_bytes_process"] = self._peak_ram_bytes
        snapshot["peak_vram_bytes_device"] = self._peak_vram_bytes
        self._last_snapshot = dict(snapshot)
        return dict(snapshot)

    def summary(self) -> dict[str, int | float | None]:
        """Return observed peaks and elapsed time; does not claim unobserved peaks."""
        last = self.sample()
        return {"duration_seconds": last["timestamp_seconds"],
                "peak_ram_bytes_process": self._peak_ram_bytes,
                "peak_vram_bytes_device": self._peak_vram_bytes}
