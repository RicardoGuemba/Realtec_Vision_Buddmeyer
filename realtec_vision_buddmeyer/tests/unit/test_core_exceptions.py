# -*- coding: utf-8 -*-
"""Testes unitários para core.exceptions."""

import pytest

from core.exceptions import (
    BuddmeyerVisionError,
    ConfigurationError,
    StreamError,
    DetectionError,
    CIPError,
    RobotControlError,
    StateTransitionError,
)


class TestExceptionsHierarchy:
    """Testes da hierarquia de exceções."""

    def test_base_exception(self):
        e = BuddmeyerVisionError("msg")
        assert str(e) == "msg"
        assert e.details == {}

    def test_base_with_details(self):
        e = BuddmeyerVisionError("msg", details={"key": "value"})
        assert "Details" in str(e)
        assert e.details["key"] == "value"

    def test_configuration_error_inherits(self):
        with pytest.raises(ConfigurationError) as exc:
            raise ConfigurationError("config err")
        assert isinstance(exc.value, BuddmeyerVisionError)

    def test_stream_error_inherits(self):
        with pytest.raises(StreamError) as exc:
            raise StreamError("stream err")
        assert isinstance(exc.value, BuddmeyerVisionError)

    def test_detection_error_inherits(self):
        with pytest.raises(DetectionError) as exc:
            raise DetectionError("det err")
        assert isinstance(exc.value, BuddmeyerVisionError)

    def test_cip_error_inherits(self):
        with pytest.raises(CIPError) as exc:
            raise CIPError("cip err")
        assert isinstance(exc.value, BuddmeyerVisionError)

    def test_state_transition_inherits_robot(self):
        with pytest.raises(StateTransitionError) as exc:
            raise StateTransitionError("trans err")
        assert isinstance(exc.value, RobotControlError)
        assert isinstance(exc.value, BuddmeyerVisionError)
