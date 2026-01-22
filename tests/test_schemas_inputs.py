"""Tests for input schemas."""

import pytest
from pydantic import ValidationError
from src.reqgate.schemas.inputs import RequirementPacket


class TestRequirementPacket:
    """Test suite for RequirementPacket schema."""

    def test_valid_packet_minimal(self):
        """Test creating a valid packet with minimal required fields."""
        packet = RequirementPacket(
            raw_text="This is a valid requirement text",
            source_type="Jira_Ticket",
            project_key="PAY",
        )

        assert packet.raw_text == "This is a valid requirement text"
        assert packet.source_type == "Jira_Ticket"
        assert packet.project_key == "PAY"
        assert packet.priority == "P1"  # default
        assert packet.ticket_type == "Feature"  # default
        assert packet.attachments == []  # default

    def test_valid_packet_full(self):
        """Test creating a valid packet with all fields."""
        packet = RequirementPacket(
            raw_text="实现用户登录功能，支持邮箱和手机号登录",
            source_type="PRD_Doc",
            project_key="AUTH",
            priority="P0",
            ticket_type="Bug",
            attachments=["https://example.com/doc.pdf"],
        )

        assert packet.priority == "P0"
        assert packet.ticket_type == "Bug"
        assert len(packet.attachments) == 1

    def test_invalid_raw_text_too_short(self):
        """Test that raw_text with less than 10 characters fails."""
        with pytest.raises(ValidationError) as exc_info:
            RequirementPacket(
                raw_text="short",
                source_type="Jira_Ticket",
                project_key="PAY",
            )

        assert "raw_text" in str(exc_info.value)

    def test_invalid_raw_text_empty(self):
        """Test that empty raw_text fails."""
        with pytest.raises(ValidationError):
            RequirementPacket(
                raw_text="",
                source_type="Jira_Ticket",
                project_key="PAY",
            )

    def test_invalid_raw_text_whitespace_only(self):
        """Test that whitespace-only raw_text fails."""
        with pytest.raises(ValidationError):
            RequirementPacket(
                raw_text="          ",
                source_type="Jira_Ticket",
                project_key="PAY",
            )

    def test_raw_text_strips_whitespace(self):
        """Test that raw_text is stripped of leading/trailing whitespace."""
        packet = RequirementPacket(
            raw_text="  This is a valid requirement text  ",
            source_type="Jira_Ticket",
            project_key="PAY",
        )

        assert packet.raw_text == "This is a valid requirement text"

    def test_invalid_source_type(self):
        """Test that invalid source_type fails."""
        with pytest.raises(ValidationError):
            RequirementPacket(
                raw_text="This is a valid requirement text",
                source_type="Invalid_Source",
                project_key="PAY",
            )

    def test_valid_source_types(self):
        """Test all valid source types."""
        for source_type in ["Jira_Ticket", "PRD_Doc", "Meeting_Transcript"]:
            packet = RequirementPacket(
                raw_text="This is a valid requirement text",
                source_type=source_type,
                project_key="PAY",
            )
            assert packet.source_type == source_type

    def test_invalid_project_key_lowercase(self):
        """Test that lowercase project_key fails."""
        with pytest.raises(ValidationError):
            RequirementPacket(
                raw_text="This is a valid requirement text",
                source_type="Jira_Ticket",
                project_key="pay",
            )

    def test_invalid_project_key_too_short(self):
        """Test that project_key with less than 2 chars fails."""
        with pytest.raises(ValidationError):
            RequirementPacket(
                raw_text="This is a valid requirement text",
                source_type="Jira_Ticket",
                project_key="P",
            )

    def test_invalid_project_key_too_long(self):
        """Test that project_key with more than 5 chars fails."""
        with pytest.raises(ValidationError):
            RequirementPacket(
                raw_text="This is a valid requirement text",
                source_type="Jira_Ticket",
                project_key="TOOLONG",
            )

    def test_valid_project_keys(self):
        """Test valid project key lengths."""
        for key in ["PA", "PAY", "AUTH", "PROJE"]:
            packet = RequirementPacket(
                raw_text="This is a valid requirement text",
                source_type="Jira_Ticket",
                project_key=key,
            )
            assert packet.project_key == key

    def test_invalid_priority(self):
        """Test that invalid priority fails."""
        with pytest.raises(ValidationError):
            RequirementPacket(
                raw_text="This is a valid requirement text",
                source_type="Jira_Ticket",
                project_key="PAY",
                priority="P3",
            )

    def test_invalid_ticket_type(self):
        """Test that invalid ticket_type fails."""
        with pytest.raises(ValidationError):
            RequirementPacket(
                raw_text="This is a valid requirement text",
                source_type="Jira_Ticket",
                project_key="PAY",
                ticket_type="Task",
            )

    def test_invalid_attachment_url(self):
        """Test that invalid attachment URL fails."""
        with pytest.raises(ValidationError):
            RequirementPacket(
                raw_text="This is a valid requirement text",
                source_type="Jira_Ticket",
                project_key="PAY",
                attachments=["not-a-url"],
            )

    def test_json_serialization(self):
        """Test that packet can be serialized to JSON."""
        packet = RequirementPacket(
            raw_text="This is a valid requirement text",
            source_type="Jira_Ticket",
            project_key="PAY",
        )

        json_str = packet.model_dump_json()
        assert "raw_text" in json_str
        assert "source_type" in json_str
