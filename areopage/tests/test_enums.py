from areopage import (
    AgentName,
    FindingCategory,
    ReviewPosition,
    Severity,
    SessionStatus,
)


def test_agent_names():
    assert set(AgentName) == {AgentName.CLAUDE_CODE, AgentName.CODEX_CLI}


def test_enums_are_str_valued():
    for enum_cls in (AgentName, Severity, FindingCategory, ReviewPosition, SessionStatus):
        for member in enum_cls:
            assert isinstance(member, str)
            assert member.value == str(member)


def test_review_positions_cover_spec():
    assert {p.value for p in ReviewPosition} == {"confirmed", "corrected", "rejected"}


def test_session_status_lifecycle_members():
    values = {s.value for s in SessionStatus}
    assert {"created", "first_round", "review", "second_round", "completed", "failed"} == values
