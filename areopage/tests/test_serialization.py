import json

from areopage import CouncilSession, Finding, SourceDocument


def test_stable_json_is_deterministic(document: SourceDocument):
    assert document.to_stable_json() == document.to_stable_json()


def test_stable_json_keys_sorted(finding: Finding):
    payload = json.loads(finding.to_stable_json())
    assert list(payload.keys()) == sorted(payload.keys())


def test_round_trip_document(document: SourceDocument):
    restored = SourceDocument.from_json(document.to_stable_json())
    assert restored == document
    assert restored.to_stable_json() == document.to_stable_json()


def test_round_trip_full_session(document, finding, confidence):
    from areopage import AgentName, FirstRoundAnalysis

    session = CouncilSession(
        document=document,
        first_round=[
            FirstRoundAnalysis(
                agent=AgentName.CLAUDE_CODE,
                document_id=document.id,
                findings=[finding],
                summary="Résumé de premier tour.",
                confidence=confidence,
            )
        ],
    )
    restored = CouncilSession.from_json(session.to_stable_json())
    assert restored == session


def test_json_uses_plain_string_enums_and_uuids(finding: Finding):
    payload = json.loads(finding.to_stable_json())
    assert payload["author"] == "claude_code"
    assert isinstance(payload["id"], str)
    assert payload["created_at"].endswith("Z") or "+" in payload["created_at"]
