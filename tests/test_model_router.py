import pytest

from jarvis.brain.model_router import ModelRouter


def test_model_router_initializes():
    router = ModelRouter(
        provider="gemini",
        primary_model="gemini-pro-latest",
        fallback_model="gemini-pro-latest",
        nvidia_model="nvidia/nemotron",
        omniroute_model="omniroute/default",
    )
    assert router is not None
    assert router.provider == "gemini"


def test_resolve_model_gemini():
    router = ModelRouter(
        provider="gemini",
        primary_model="gemini-pro-latest",
        fallback_model="gemini-pro-latest",
        nvidia_model="nvidia/nemotron",
        omniroute_model="omniroute/default",
    )
    assert router.resolve_model("gemini") == "gemini-pro-latest"


def test_resolve_model_nvidia():
    router = ModelRouter(
        provider="gemini",
        primary_model="gemini-pro-latest",
        fallback_model="gemini-pro-latest",
        nvidia_model="nvidia/nemotron",
        omniroute_model="omniroute/default",
    )
    assert router.resolve_model("nvidia") == "nvidia/nemotron"


def test_resolve_model_omniroute():
    router = ModelRouter(
        provider="gemini",
        primary_model="gemini-pro-latest",
        fallback_model="gemini-pro-latest",
        nvidia_model="nvidia/nemotron",
        omniroute_model="omniroute/default",
    )
    assert router.resolve_model("omniroute") == "omniroute/default"


def test_set_providers_and_resolve_fallback():
    router = ModelRouter(
        provider="gemini",
        primary_model="gemini-pro-latest",
        fallback_model="gemini-pro-latest",
        nvidia_model="nvidia/nemotron",
        omniroute_model="omniroute/default",
    )
    router.set_providers(["gemini", "nvidia", "omniroute"])
    assert router.resolve_fallback("gemini") == "nvidia"
    assert router.resolve_fallback("nvidia") == "omniroute"
    assert router.resolve_fallback("omniroute") is None
