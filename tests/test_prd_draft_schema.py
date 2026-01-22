"""Tests for PRD_Draft schema validation."""

import pytest
from pydantic import ValidationError
from src.reqgate.schemas.internal import PRD_Draft


class TestPRDDraftValid:
    """Tests for valid PRD_Draft instances."""

    def test_minimal_valid_prd(self) -> None:
        """Test PRD_Draft with only required fields."""
        prd = PRD_Draft(
            title="Implement user login feature",
            user_story="As a user, I want to log in, so that I can access my account",
            acceptance_criteria=["User can enter username and password"],
        )
        assert prd.title == "Implement user login feature"
        assert prd.user_story == "As a user, I want to log in, so that I can access my account"
        assert len(prd.acceptance_criteria) == 1
        assert prd.edge_cases == []
        assert prd.resources == []
        assert prd.missing_info == []
        assert prd.clarification_questions == []

    def test_full_valid_prd(self) -> None:
        """Test PRD_Draft with all fields populated."""
        prd = PRD_Draft(
            title="Implement user authentication with OAuth2",
            user_story="As a user, I want to log in with Google, so that I don't need to create a new password",
            acceptance_criteria=[
                "User can click 'Sign in with Google' button",
                "System redirects to Google OAuth consent screen",
                "After approval, user is logged into the application",
            ],
            edge_cases=[
                "User denies OAuth consent",
                "Google service is down",
            ],
            resources=[
                "OAuth2 RFC 6749",
                "Google OAuth documentation",
            ],
            missing_info=["Session timeout duration not specified"],
            clarification_questions=["Should we support other OAuth providers?"],
        )
        assert prd.title == "Implement user authentication with OAuth2"
        assert len(prd.acceptance_criteria) == 3
        assert len(prd.edge_cases) == 2
        assert len(prd.resources) == 2
        assert len(prd.missing_info) == 1
        assert len(prd.clarification_questions) == 1

    def test_various_action_verbs(self) -> None:
        """Test that various action verbs are accepted in title."""
        valid_titles = [
            "Add new search functionality",
            "Create user profile page",
            "Build dashboard component",
            "Fix login button alignment",
            "Update database schema for users",
            "Remove deprecated API endpoint",
            "Refactor authentication module",
            "Optimize image loading performance",
            "Enable two-factor authentication",
            "Integrate payment gateway",
            "Support multiple languages",
            "Allow users to export data",
            "Introduce caching mechanism",
            "Extend API with new endpoints",
            "Enhance search with filters",
        ]
        for title in valid_titles:
            prd = PRD_Draft(
                title=title,
                user_story="As a user, I want this feature, so that I can benefit",
                acceptance_criteria=["Feature works as expected"],
            )
            assert prd.title == title


class TestPRDDraftTitleValidation:
    """Tests for title field validation."""

    def test_title_too_short(self) -> None:
        """Test that title shorter than 10 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PRD_Draft(
                title="Add foo",  # 7 chars
                user_story="As a user, I want this, so that I benefit",
                acceptance_criteria=["Something"],
            )
        assert "String should have at least 10 characters" in str(exc_info.value)

    def test_title_too_long(self) -> None:
        """Test that title longer than 200 characters is rejected."""
        long_title = "Implement " + "a" * 200
        with pytest.raises(ValidationError) as exc_info:
            PRD_Draft(
                title=long_title,
                user_story="As a user, I want this, so that I benefit",
                acceptance_criteria=["Something"],
            )
        assert "String should have at most 200 characters" in str(exc_info.value)

    def test_title_not_starting_with_action_verb(self) -> None:
        """Test that title not starting with action verb is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PRD_Draft(
                title="User login functionality needs to be done",
                user_story="As a user, I want to log in, so that I can access my account",
                acceptance_criteria=["User can log in"],
            )
        assert "Title must start with an action verb" in str(exc_info.value)

    def test_title_with_number_prefix(self) -> None:
        """Test that title starting with number is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PRD_Draft(
                title="123 Add new feature to system",
                user_story="As a user, I want this, so that I benefit",
                acceptance_criteria=["Something"],
            )
        assert "Title must start with an action verb" in str(exc_info.value)


class TestPRDDraftUserStoryValidation:
    """Tests for user_story field validation."""

    def test_user_story_too_short(self) -> None:
        """Test that user_story shorter than 20 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PRD_Draft(
                title="Implement user login",
                user_story="As a user, I want",  # 17 chars
                acceptance_criteria=["Something"],
            )
        assert "String should have at least 20 characters" in str(exc_info.value)

    def test_user_story_wrong_format_missing_as_a(self) -> None:
        """Test that user_story without 'As a' prefix is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PRD_Draft(
                title="Implement user login feature",
                user_story="I want to log in, so that I can access my account",
                acceptance_criteria=["User can log in"],
            )
        assert "User story must follow" in str(exc_info.value)

    def test_user_story_wrong_format_missing_i_want(self) -> None:
        """Test that user_story without 'I want' is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PRD_Draft(
                title="Implement user login feature",
                user_story="As a user, I need to log in, so that I can access my account",
                acceptance_criteria=["User can log in"],
            )
        assert "User story must follow" in str(exc_info.value)

    def test_user_story_wrong_format_missing_so_that(self) -> None:
        """Test that user_story without 'so that' is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PRD_Draft(
                title="Implement user login feature",
                user_story="As a user, I want to log in because I need access",
                acceptance_criteria=["User can log in"],
            )
        assert "User story must follow" in str(exc_info.value)

    def test_user_story_valid_variations(self) -> None:
        """Test valid variations of user story format."""
        valid_stories = [
            "As a user, I want to log in, so that I can access my account",
            "As an admin, I want to manage users, so that I can control access",
            "As a customer, I want to view my orders, so that I can track deliveries",
        ]
        for story in valid_stories:
            prd = PRD_Draft(
                title="Implement this feature",
                user_story=story,
                acceptance_criteria=["Feature works"],
            )
            assert prd.user_story == story


class TestPRDDraftAcceptanceCriteriaValidation:
    """Tests for acceptance_criteria field validation."""

    def test_acceptance_criteria_empty_list(self) -> None:
        """Test that empty acceptance_criteria list is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PRD_Draft(
                title="Implement user login feature",
                user_story="As a user, I want to log in, so that I can access",
                acceptance_criteria=[],
            )
        assert "List should have at least 1 item" in str(exc_info.value)

    def test_acceptance_criteria_empty_string_item(self) -> None:
        """Test that acceptance_criteria with empty string is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PRD_Draft(
                title="Implement user login feature",
                user_story="As a user, I want to log in, so that I can access",
                acceptance_criteria=["Valid criterion", ""],
            )
        assert "cannot be empty or whitespace" in str(exc_info.value)

    def test_acceptance_criteria_whitespace_only_item(self) -> None:
        """Test that acceptance_criteria with whitespace-only string is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PRD_Draft(
                title="Implement user login feature",
                user_story="As a user, I want to log in, so that I can access",
                acceptance_criteria=["Valid criterion", "   "],
            )
        assert "cannot be empty or whitespace" in str(exc_info.value)

    def test_acceptance_criteria_multiple_items(self) -> None:
        """Test acceptance_criteria with multiple valid items."""
        prd = PRD_Draft(
            title="Implement user login feature",
            user_story="As a user, I want to log in, so that I can access my account",
            acceptance_criteria=[
                "Given valid credentials, user can log in",
                "Given invalid credentials, user sees error message",
                "User session persists for 24 hours",
            ],
        )
        assert len(prd.acceptance_criteria) == 3


class TestPRDDraftOptionalFields:
    """Tests for optional fields in PRD_Draft."""

    def test_edge_cases_default_empty(self) -> None:
        """Test that edge_cases defaults to empty list."""
        prd = PRD_Draft(
            title="Implement user login feature",
            user_story="As a user, I want to log in, so that I can access",
            acceptance_criteria=["User can log in"],
        )
        assert prd.edge_cases == []

    def test_edge_cases_with_values(self) -> None:
        """Test edge_cases with provided values."""
        prd = PRD_Draft(
            title="Implement user login feature",
            user_story="As a user, I want to log in, so that I can access",
            acceptance_criteria=["User can log in"],
            edge_cases=["Server timeout", "Invalid token"],
        )
        assert prd.edge_cases == ["Server timeout", "Invalid token"]

    def test_resources_default_empty(self) -> None:
        """Test that resources defaults to empty list."""
        prd = PRD_Draft(
            title="Implement user login feature",
            user_story="As a user, I want to log in, so that I can access",
            acceptance_criteria=["User can log in"],
        )
        assert prd.resources == []

    def test_missing_info_with_values(self) -> None:
        """Test missing_info with provided values."""
        prd = PRD_Draft(
            title="Implement user login feature",
            user_story="As a user, I want to log in, so that I can access",
            acceptance_criteria=["User can log in"],
            missing_info=["Session timeout duration", "Password requirements"],
        )
        assert len(prd.missing_info) == 2

    def test_clarification_questions_with_values(self) -> None:
        """Test clarification_questions with provided values."""
        prd = PRD_Draft(
            title="Implement user login feature",
            user_story="As a user, I want to log in, so that I can access",
            acceptance_criteria=["User can log in"],
            clarification_questions=["Should we support SSO?", "Max login attempts?"],
        )
        assert len(prd.clarification_questions) == 2


class TestPRDDraftSerialization:
    """Tests for PRD_Draft serialization."""

    def test_json_serialization(self) -> None:
        """Test that PRD_Draft can be serialized to JSON."""
        prd = PRD_Draft(
            title="Implement user login feature",
            user_story="As a user, I want to log in, so that I can access my account",
            acceptance_criteria=["User can log in", "Session is created"],
            edge_cases=["Invalid credentials"],
        )
        json_str = prd.model_dump_json()
        assert "Implement user login feature" in json_str
        assert "User can log in" in json_str

    def test_dict_serialization(self) -> None:
        """Test that PRD_Draft can be serialized to dict."""
        prd = PRD_Draft(
            title="Implement user login feature",
            user_story="As a user, I want to log in, so that I can access my account",
            acceptance_criteria=["User can log in"],
        )
        data = prd.model_dump()
        assert data["title"] == "Implement user login feature"
        assert data["acceptance_criteria"] == ["User can log in"]
        assert data["edge_cases"] == []

    def test_from_dict(self) -> None:
        """Test that PRD_Draft can be created from dict."""
        data = {
            "title": "Implement user login feature",
            "user_story": "As a user, I want to log in, so that I can access my account",
            "acceptance_criteria": ["User can log in"],
        }
        prd = PRD_Draft.model_validate(data)
        assert prd.title == "Implement user login feature"

    def test_schema_example(self) -> None:
        """Test that schema example is valid."""
        schema = PRD_Draft.model_json_schema()
        example = schema.get("example") or schema.get("examples", [{}])[0]
        # The example should be valid
        prd = PRD_Draft.model_validate(example)
        assert prd.title == "Implement user authentication with OAuth2"
