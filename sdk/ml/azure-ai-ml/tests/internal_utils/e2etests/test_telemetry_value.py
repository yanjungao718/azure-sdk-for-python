# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import pytest

from .._util import _UTILS_TIMEOUT_SECOND


@pytest.mark.timeout(_UTILS_TIMEOUT_SECOND)
@pytest.mark.e2etest
class TestTelemetryValue:
    def test_component_node_telemetry_value(self, hello_world_component):
        # From remote
        v = hello_world_component._get_telemetry_values()
        assert v["type"] == "command"
        assert v["source"] == "REMOTE.WORKSPACE.COMPONENT"
        assert v["is_anonymous"] is False
        component = hello_world_component()
        v = component._get_telemetry_values()
        assert v["type"] == "command"
        assert v["source"] == "REMOTE.WORKSPACE.COMPONENT"
