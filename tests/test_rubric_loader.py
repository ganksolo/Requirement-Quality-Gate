"""Tests for RubricLoader."""



from src.reqgate.gates.rules import RubricLoader, get_rubric_loader


class TestRubricLoader:
    """Test suite for RubricLoader class."""

    def test_load_rubric_file(self):
        """Test that rubric file is loaded correctly."""
        loader = RubricLoader()
        rubric = loader.load()

        assert "FEATURE" in rubric
        assert "BUG" in rubric

    def test_feature_config_structure(self):
        """Test FEATURE config has required fields."""
        loader = RubricLoader()
        rubric = loader.load()
        feature = rubric["FEATURE"]

        assert "threshold" in feature
        assert "weights" in feature
        assert "required_fields" in feature
        assert "negative_patterns" in feature

    def test_bug_config_structure(self):
        """Test BUG config has required fields."""
        loader = RubricLoader()
        rubric = loader.load()
        bug = rubric["BUG"]

        assert "threshold" in bug
        assert "weights" in bug
        assert "required_fields" in bug

    def test_feature_threshold(self):
        """Test FEATURE threshold value."""
        loader = RubricLoader()
        rubric = loader.load()

        assert rubric["FEATURE"]["threshold"] == 60

    def test_bug_threshold(self):
        """Test BUG threshold value."""
        loader = RubricLoader()
        rubric = loader.load()

        assert rubric["BUG"]["threshold"] == 50

    def test_get_scenario_config_feature(self):
        """Test get_scenario_config for Feature type."""
        loader = RubricLoader()
        config = loader.get_scenario_config("Feature")

        assert config["threshold"] == 60
        assert "completeness" in config["weights"]

    def test_get_scenario_config_bug(self):
        """Test get_scenario_config for Bug type."""
        loader = RubricLoader()
        config = loader.get_scenario_config("Bug")

        assert config["threshold"] == 50
        assert "reproduction" in config["weights"]

    def test_get_scenario_config_non_bug_maps_to_feature(self):
        """Test that non-Bug ticket types map to FEATURE."""
        loader = RubricLoader()

        # "Unknown" maps to FEATURE (not Bug)
        config = loader.get_scenario_config("Unknown")
        assert config["threshold"] == 60  # FEATURE threshold

    def test_caching_behavior(self):
        """Test that rubric is cached after first load."""
        loader = RubricLoader()

        # First load
        rubric1 = loader.load()
        # Second load should use cache
        rubric2 = loader.load()

        assert rubric1 is rubric2


class TestGetRubricLoader:
    """Test suite for get_rubric_loader singleton."""

    def test_returns_loader_instance(self):
        """Test that get_rubric_loader returns a RubricLoader."""
        get_rubric_loader.cache_clear()

        loader = get_rubric_loader()
        assert isinstance(loader, RubricLoader)

    def test_singleton_behavior(self):
        """Test singleton pattern."""
        get_rubric_loader.cache_clear()

        loader1 = get_rubric_loader()
        loader2 = get_rubric_loader()

        assert loader1 is loader2
