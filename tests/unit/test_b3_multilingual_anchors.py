"""Tests for B3 intervention: Multilingual anchor support.

Verifies that Spanish queries are properly translated and matched.
"""

import pytest
from src.domain.anchor_extractor import extract_anchors


class TestB3MultilingualSupport:
    """Test B3 intervention: Spanish -> English translation for anchors."""

    def test_spanish_servicio_translated_to_service(self):
        """Spanish 'servicio' is translated to 'service' for matching."""
        anchors_cfg = {
            "multilingual": {"servicio": "service"},
            "anchors": {
                "strong": {"files": [], "dirs": [], "exts": [], "symbols_terms": ["service"]},
                "weak": {"intent_terms": [], "doc_terms": []},
            },
        }
        aliases_cfg = {}

        result = extract_anchors("servicio", anchors_cfg, aliases_cfg)

        # Should detect 'service' after translation
        assert "service" in result["tokens"]
        assert "service" in result["strong"]

    def test_spanish_documentacion_translated(self):
        """Spanish 'documentación' is translated to 'documentation'."""
        anchors_cfg = {
            "multilingual": {"documentación": "documentation"},
            "anchors": {
                "strong": {"files": [], "dirs": [], "exts": [], "symbols_terms": ["documentation"]},
                "weak": {"intent_terms": [], "doc_terms": []},
            },
        }
        aliases_cfg = {}

        result = extract_anchors("documentación", anchors_cfg, aliases_cfg)

        assert "documentation" in result["tokens"]

    def test_mixed_spanish_english_query(self):
        """Mixed Spanish/English queries are properly handled."""
        anchors_cfg = {
            "multilingual": {"servicio": "service", "cómo": "how"},
            "anchors": {
                "strong": {"files": [], "dirs": [], "exts": [], "symbols_terms": ["service"]},
                "weak": {"intent_terms": ["how"], "doc_terms": []},
            },
        }
        aliases_cfg = {}

        result = extract_anchors("cómo usar servicio", anchors_cfg, aliases_cfg)

        # Both Spanish terms should be translated
        assert "service" in result["tokens"]
        assert "how" in result["tokens"]
        assert "how" in result["weak"]

    def test_english_query_unchanged(self):
        """English queries pass through unchanged."""
        anchors_cfg = {
            "multilingual": {"servicio": "service"},
            "anchors": {
                "strong": {"files": [], "dirs": [], "exts": [], "symbols_terms": ["service"]},
                "weak": {"intent_terms": [], "doc_terms": []},
            },
        }
        aliases_cfg = {}

        result = extract_anchors("service", anchors_cfg, aliases_cfg)

        assert "service" in result["tokens"]
        assert "service" in result["strong"]

    def test_no_multilingual_config(self):
        """Works without multilingual config (backward compatible)."""
        anchors_cfg = {
            "anchors": {
                "strong": {"files": [], "dirs": [], "exts": [], "symbols_terms": ["service"]},
                "weak": {"intent_terms": [], "doc_terms": []},
            },
        }
        aliases_cfg = {}

        result = extract_anchors("servicio", anchors_cfg, aliases_cfg)

        # Should still work, just without translation
        assert "servicio" in result["tokens"]
        # Won't match 'service' since no translation
        assert "service" not in result["strong"]

    def test_spanish_phrase_matching(self):
        """Spanish phrases in query are translated for substring matching."""
        anchors_cfg = {
            "multilingual": {"guía": "guide"},
            "anchors": {
                "strong": {"files": [], "dirs": [], "exts": [], "symbols_terms": ["guide"]},
                "weak": {"intent_terms": [], "doc_terms": []},
            },
        }
        aliases_cfg = {}

        result = extract_anchors("la guía de usuario", anchors_cfg, aliases_cfg)

        # 'guide' should be detected after translation
        assert "guide" in result["tokens"]
        assert "guide" in result["strong"]


class TestB3RealWorldScenarios:
    """Test real-world scenarios from telemetry data."""

    def test_servicio_zero_hit_scenario(self):
        """Reproduce and fix the 'servicio' zero-hit scenario from telemetry."""
        anchors_cfg = {
            "multilingual": {
                "servicio": "service",
                "servicios": "services",
            },
            "anchors": {
                "strong": {
                    "files": ["service.md"],
                    "dirs": ["services/"],
                    "exts": [],
                    "symbols_terms": ["service"],
                },
                "weak": {"intent_terms": [], "doc_terms": []},
            },
        }
        aliases_cfg = {}

        # This was returning 0 hits before B3
        result = extract_anchors("servicio", anchors_cfg, aliases_cfg)

        # After translation, should match service-related anchors
        assert "service" in result["tokens"]
        assert any("service" in s for s in result["strong"])

    def test_documentacion_intent(self):
        """Spanish documentation query matches documentation anchors."""
        anchors_cfg = {
            "multilingual": {
                "documentación": "documentation",
                "manual": "manual",
            },
            "anchors": {
                "strong": {
                    "files": ["README.md"],
                    "dirs": ["docs/"],
                    "exts": [],
                    "symbols_terms": [],
                },
                "weak": {"intent_terms": [], "doc_terms": ["documentation", "manual"]},
            },
        }
        aliases_cfg = {}

        result = extract_anchors("documentación del sistema", anchors_cfg, aliases_cfg)

        assert "documentation" in result["weak"]
