# Prompt Templates Documentation

> This document describes the prompt templates used in ReqGate for LLM interactions.

## Overview

ReqGate uses carefully crafted prompts for LLM-based components. All prompts are stored in the `prompts/` directory to enable:
- Version control
- Easy modification without code changes
- A/B testing (future)
- Prompt optimization tracking

## Prompt Files

| File | Component | Purpose |
|------|-----------|---------|
| `structuring_agent_v1.txt` | Structuring Agent | Convert raw text to PRD_Draft |

## Structuring Agent Prompt

**File**: `prompts/structuring_agent_v1.txt`

### Purpose

Transforms unstructured requirement text (meeting notes, emails, rough ideas) into a standardized PRD format that can be evaluated by the Scoring Agent.

### Template Variables

| Variable | Description | Source |
|----------|-------------|--------|
| `{input_text}` | Raw requirement text | `RequirementPacket.raw_text` |
| `{prd_draft_schema}` | JSON schema for PRD_Draft | Generated from Pydantic model |
| `{example_output}` | Example PRD_Draft JSON | Predefined example |

### Key Sections

#### 1. Role Definition
```
You are a requirements structuring assistant. Your job is to extract 
structured information from unstructured requirement text.
```

#### 2. Critical Rules (Anti-Hallucination)
```
1. ONLY extract information explicitly present in the input
2. DO NOT invent, assume, or hallucinate details
3. If information is missing, add it to "missing_info" field
4. If clarification is needed, add specific questions to "clarification_questions"
5. Use exact quotes from the input when possible
```

#### 3. Extraction Guidelines

For each field, specific instructions are provided:

**Title**:
- Start with action verb (Implement, Add, Create, Fix, Update)
- 10-200 characters
- Specific and descriptive

**User Story**:
- Format: "As a [role], I want [feature], so that [benefit]"
- Infer from context if not explicit
- Mark as needing clarification if unclear

**Acceptance Criteria**:
- Discrete, testable statements
- Given/When/Then format preferred
- Minimum 1 required
- Add to missing_info if none found

**Edge Cases**:
- Only mentioned scenarios
- NO invented scenarios
- Empty if none mentioned

**Resources**:
- URLs, ticket references, documentation links
- Dependencies mentioned
- Empty if none

**Missing Info**:
- Critical information not provided
- Common items: acceptance_criteria, error_handling, performance_requirements

**Clarification Questions**:
- Specific, actionable questions
- Fill identified gaps

### Anti-Hallucination Techniques

1. **Explicit Instructions**: Multiple warnings against inventing content
2. **Quote Requirement**: "Use exact quotes from the input when possible"
3. **Missing Info Field**: Provides outlet for gaps instead of filling them
4. **Schema Validation**: Output must match PRD_Draft schema
5. **Temperature=0**: Deterministic, consistent extraction

### Example Usage

**Input**:
```
We need to add a feature where users can export their data. They should 
be able to download all their profile information and activity history 
as a CSV file. This is for GDPR compliance.
```

**Output**:
```json
{
  "title": "Implement User Data Export for GDPR Compliance",
  "user_story": "As a user, I want to export my data as CSV, so that I can have a copy of my personal information for GDPR compliance",
  "acceptance_criteria": [
    "User can export profile information as CSV",
    "User can export activity history as CSV",
    "Export includes all personal data"
  ],
  "edge_cases": [],
  "resources": [],
  "missing_info": [
    "acceptance_criteria - specific format requirements not defined",
    "performance_requirements - file size limits not specified"
  ],
  "clarification_questions": [
    "Should the exports be combined or separate files?",
    "What is the maximum data retention period to include?"
  ]
}
```

## Scoring Agent Prompt

The Scoring Agent uses a dynamic prompt built from:
1. System instructions for scoring
2. The scoring rubric from YAML configuration
3. Input text (either PRD_Draft or raw text in fallback mode)

### Prompt Building

```python
def build_scoring_prompt(prd_text: str, rubric: RubricConfig) -> str:
    return f"""
    You are a requirement quality evaluator.
    
    Evaluate the following requirement against these criteria:
    {format_rubric(rubric)}
    
    Requirement:
    {prd_text}
    
    Provide scores and issues in JSON format matching TicketScoreReport schema.
    """
```

### Fallback Mode

When structuring fails, the Scoring Agent receives raw text:

```python
if fallback_activated:
    input_text = packet.raw_text
    # Note: Score penalty applied separately
else:
    input_text = format_prd_for_scoring(structured_prd)
```

## Best Practices

### Prompt Design

1. **Clear Role**: Define exactly what the LLM should do
2. **Explicit Constraints**: State what NOT to do
3. **Structured Output**: Use JSON schema for consistent parsing
4. **Examples**: Provide concrete examples
5. **Fallback Handling**: Guide behavior for edge cases

### Version Control

- Keep prompts in separate files, not inline code
- Use semantic versioning (v1, v2, etc.)
- Document changes in commit messages
- Test changes with golden test sets

### Performance

- Keep prompts concise (reduce tokens)
- Use structured output format (JSON mode)
- Minimize few-shot examples (increase if quality issues)

## Future Enhancements

- **Prompt A/B Testing**: Compare versions on same inputs
- **Automated Optimization**: Use feedback to improve prompts
- **Multi-Language Support**: Localized prompts
- **Prompt Library**: Reusable prompt components
