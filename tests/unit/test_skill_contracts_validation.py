"""Unit tests for skill contracts validation (domain layer, pure Python)."""


class TestSkillInputValidation:
    """Tests for SkillInput validation."""

    def test_valid_string_input(self):
        """Valid string input should pass."""
        from src.domain.skill_contracts import SkillInput, validate_skill_input

        inp = SkillInput(name="query", type="string", required=True)
        result = validate_skill_input(inp)
        assert result.is_ok()
        assert result.unwrap().name == "query"

    def test_valid_file_input(self):
        """Valid file input should pass."""
        from src.domain.skill_contracts import SkillInput, validate_skill_input

        inp = SkillInput(name="context", type="file", required=False)
        result = validate_skill_input(inp)
        assert result.is_ok()
        assert result.unwrap().type == "file"

    def test_valid_json_input(self):
        """Valid json input should pass."""
        from src.domain.skill_contracts import SkillInput, validate_skill_input

        inp = SkillInput(name="data", type="json", required=True)
        result = validate_skill_input(inp)
        assert result.is_ok()

    def test_valid_boolean_input(self):
        """Valid boolean input should pass."""
        from src.domain.skill_contracts import SkillInput, validate_skill_input

        inp = SkillInput(name="flag", type="boolean", required=False)
        result = validate_skill_input(inp)
        assert result.is_ok()

    def test_valid_number_input(self):
        """Valid number input should pass."""
        from src.domain.skill_contracts import SkillInput, validate_skill_input

        inp = SkillInput(name="count", type="number", required=True)
        result = validate_skill_input(inp)
        assert result.is_ok()

    def test_invalid_type_rejected(self):
        """Invalid input type should be rejected."""
        from src.domain.skill_contracts import SkillInput, validate_skill_input

        inp = SkillInput(name="bad", type="invalid_type", required=True)
        result = validate_skill_input(inp)
        assert result.is_err()
        errors = result.unwrap_err()
        assert any("type" in str(e).lower() for e in errors)

    def test_empty_name_rejected(self):
        """Empty input name should be rejected."""
        from src.domain.skill_contracts import SkillInput, validate_skill_input

        inp = SkillInput(name="", type="string", required=True)
        result = validate_skill_input(inp)
        assert result.is_err()
        errors = result.unwrap_err()
        assert any("name" in str(e).lower() for e in errors)


class TestSkillMetaValidation:
    """Tests for SkillMeta validation."""

    def test_minimal_valid_meta(self):
        """Minimal valid skill metadata."""
        from src.domain.skill_contracts import SkillMeta, validate_skill_meta

        meta = SkillMeta(name="test-skill", description="Test")
        result = validate_skill_meta(meta)
        assert result.is_ok()
        validated = result.unwrap()
        assert validated.name == "test-skill"
        assert validated.description == "Test"
        assert validated.requires == []
        assert validated.inputs == []

    def test_full_valid_meta(self):
        """Full valid skill metadata with all fields."""
        from src.domain.skill_contracts import SkillMeta, SkillInput, validate_skill_meta

        meta = SkillMeta(
            name="full-skill",
            description="Full skill",
            requires=["dep1", "dep2"],
            inputs=[
                SkillInput(name="q", type="string", required=True),
                SkillInput(name="f", type="file", required=False),
            ],
            outputs=["result", "log"],
            levels=["L0", "L1", "L2"],
        )
        result = validate_skill_meta(meta)
        assert result.is_ok()
        validated = result.unwrap()
        assert len(validated.requires) == 2
        assert len(validated.inputs) == 2
        assert len(validated.outputs) == 2

    def test_empty_name_rejected(self):
        """Empty name should be rejected."""
        from src.domain.skill_contracts import SkillMeta, validate_skill_meta

        meta = SkillMeta(name="", description="Has desc")
        result = validate_skill_meta(meta)
        assert result.is_err()
        errors = result.unwrap_err()
        assert any("name" in str(e).lower() for e in errors)

    def test_whitespace_only_name_rejected(self):
        """Whitespace-only name should be rejected."""
        from src.domain.skill_contracts import SkillMeta, validate_skill_meta

        meta = SkillMeta(name="   ", description="Has desc")
        result = validate_skill_meta(meta)
        assert result.is_err()
        errors = result.unwrap_err()
        assert any("name" in str(e).lower() for e in errors)

    def test_empty_description_rejected(self):
        """Empty description should be rejected."""
        from src.domain.skill_contracts import SkillMeta, validate_skill_meta

        meta = SkillMeta(name="has-name", description="")
        result = validate_skill_meta(meta)
        assert result.is_err()
        errors = result.unwrap_err()
        assert any("description" in str(e).lower() for e in errors)

    def test_invalid_input_in_meta_rejected(self):
        """Invalid input within meta should be rejected."""
        from src.domain.skill_contracts import SkillMeta, SkillInput, validate_skill_meta

        meta = SkillMeta(
            name="test",
            description="test",
            inputs=[SkillInput(name="bad", type="invalid", required=True)],
        )
        result = validate_skill_meta(meta)
        assert result.is_err()
        errors = result.unwrap_err()
        assert any("type" in str(e).lower() for e in errors)


class TestValidateSkillMetaFunction:
    """Tests for the validate_skill_meta function."""

    def test_returns_result_type(self):
        """Should return Result type."""
        from src.domain.skill_contracts import SkillMeta, validate_skill_meta

        meta = SkillMeta(name="test", description="test")
        result = validate_skill_meta(meta)
        # Check it has is_ok method (Result protocol)
        assert hasattr(result, "is_ok")
        assert hasattr(result, "is_err")

    def test_valid_returns_ok(self):
        """Valid metadata should return Ok."""
        from src.domain.skill_contracts import SkillMeta, validate_skill_meta

        meta = SkillMeta(name="test", description="test")
        result = validate_skill_meta(meta)
        assert result.is_ok()
        assert result.unwrap() == meta

    def test_invalid_returns_errors_list(self):
        """Invalid metadata should return list of errors."""
        from src.domain.skill_contracts import SkillMeta, validate_skill_meta

        meta = SkillMeta(name="", description="")
        result = validate_skill_meta(meta)
        assert result.is_err()
        errors = result.unwrap_err()
        assert isinstance(errors, list)
        assert len(errors) >= 2  # Both name and description are empty

    def test_multiple_errors_collected(self):
        """All validation errors should be collected."""
        from src.domain.skill_contracts import SkillMeta, validate_skill_meta

        meta = SkillMeta(name="", description="")  # Both invalid
        result = validate_skill_meta(meta)
        errors = result.unwrap_err()
        error_fields = {e.field for e in errors}
        assert "name" in error_fields
        assert "description" in error_fields
