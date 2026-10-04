# -*- coding: utf8 -*-
from typing import Any
from research import ExampleProvider

__author__ = 'Mstislav Maslennikov'

class FakeProvider(ExampleProvider):
    def __init__(self) -> None:
        self.items = {"node-42": {"degree": 17, "label": "fraud"}}

    def get(self, example_id: str) -> Any:
        return self.items[example_id]

    def describe(self, example_id: str) -> str:
        item = self.items[example_id]
        return f"{example_id}: degree={item['degree']}, label={item['label']}"


def test_example_provider_supports_get_and_describe():
    provider: ExampleProvider = FakeProvider()

    assert provider.get("node-42") == {"degree": 17, "label": "fraud"}
    assert provider.describe("node-42") == "node-42: degree=17, label=fraud"
