from areopage import CouncilSession, SessionRepository, SessionStatus


def test_save_and_reload_session(tmp_path, document):
    db = tmp_path / "areopage.sqlite3"
    session = CouncilSession(document=document)

    with SessionRepository(db) as repo:
        repo.save(session)
        restored = repo.get(str(session.id))

    assert restored == session


def test_save_is_upsert(tmp_path, document):
    db = tmp_path / "areopage.sqlite3"
    session = CouncilSession(document=document)

    with SessionRepository(db) as repo:
        repo.save(session)
        session.status = SessionStatus.FIRST_ROUND
        repo.save(session)
        assert repo.list_ids() == [str(session.id)]
        assert repo.get(str(session.id)).status is SessionStatus.FIRST_ROUND


def test_get_unknown_returns_none(tmp_path):
    with SessionRepository(tmp_path / "vide.sqlite3") as repo:
        assert repo.get("00000000-0000-0000-0000-000000000000") is None
