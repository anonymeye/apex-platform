"""Unit tests for evaluation service."""

from uuid import uuid4

import pytest

from apex.ml.evaluation.judge import JudgeResult
from apex.services.evaluation_service import EvaluationService, ScopeItem


@pytest.fixture
def org_id():
    return uuid4()


@pytest.fixture
def judge_snapshot():
    return {
        "model": "gpt-4o-mini",
        "provider": "openai",
        "prompt_template": "Score: {{ user_message }} {{ agent_response }}",
        "rubric": None,
    }


@pytest.mark.asyncio
async def test_create_run(org_id, judge_snapshot):
    """create_run creates a run with scope and snapshot."""
    created_run = None

    class FakeRunRepo:
        async def create(self, **kwargs):
            nonlocal created_run
            from apex.models.evaluation import EvaluationRun
            created_run = type("Run", (), {"id": uuid4(), **kwargs})()
            return created_run

        async def get_with_scores(self, id):
            return None

        async def update(self, id, **kwargs):
            pass

    class FakeScoreRepo:
        async def create(self, **kwargs):
            pass

    svc = EvaluationService(
        run_repo=FakeRunRepo(),
        score_repo=FakeScoreRepo(),
        conversation_state_store=None,
    )
    run = await svc.create_run(
        scope_type="single",
        scope_payload={"inline": {"user_message": "Hi", "agent_response": "Hello"}, "conversation_id": str(uuid4())},
        judge_config_snapshot=judge_snapshot,
        organization_id=org_id,
    )
    assert run is not None
    assert created_run is not None
    assert created_run.scope_type == "single"
    assert created_run.status == "pending"
    assert created_run.judge_config_snapshot == judge_snapshot


@pytest.mark.asyncio
async def test_resolve_scope_items_single_inline():
    """resolve_scope_items for single+inline returns one ScopeItem."""
    class FakeRunRepo:
        pass

    class FakeScoreRepo:
        pass

    svc = EvaluationService(
        run_repo=FakeRunRepo(),
        score_repo=FakeScoreRepo(),
        conversation_state_store=None,
    )
    conv_id = uuid4()
    items = await svc.resolve_scope_items(
        "single",
        {
            "conversation_id": str(conv_id),
            "inline": {
                "user_message": "What is 2+2?",
                "agent_response": "4",
                "tool_calls_summary": None,
            },
        },
    )
    assert len(items) == 1
    assert items[0].conversation_id == conv_id
    assert items[0].turn_index == 0
    assert items[0].turn.user_message == "What is 2+2?"
    assert items[0].turn.agent_response == "4"


@pytest.mark.asyncio
async def test_resolve_scope_items_batch_inline():
    """resolve_scope_items for batch with inline items returns multiple ScopeItems."""
    class FakeRunRepo:
        pass

    class FakeScoreRepo:
        pass

    svc = EvaluationService(
        run_repo=FakeRunRepo(),
        score_repo=FakeScoreRepo(),
        conversation_state_store=None,
    )
    c1, c2 = uuid4(), uuid4()
    items = await svc.resolve_scope_items(
        "batch",
        {
            "items": [
                {"conversation_id": str(c1), "inline": {"user_message": "Q1", "agent_response": "A1"}},
                {"conversation_id": str(c2), "inline": {"user_message": "Q2", "agent_response": "A2"}},
            ],
        },
    )
    assert len(items) == 2
    assert items[0].conversation_id == c1 and items[0].turn.agent_response == "A1"
    assert items[1].conversation_id == c2 and items[1].turn.agent_response == "A2"


@pytest.mark.asyncio
async def test_resolve_scope_items_single_ref_loads_from_store():
    """resolve_scope_items for single+ref loads conversation from store."""
    from apex.storage.conversation_state import ConversationState, ConversationStateMetadata

    conv_id = uuid4()
    user_id = uuid4()
    state = ConversationState(
        messages=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there."},
        ],
        metadata=ConversationStateMetadata(
            conversation_id=str(conv_id),
            user_id=str(user_id),
            agent_id=str(uuid4()),
            created_at="",
            last_activity_at="",
            message_count=2,
        ),
    )

    class FakeStore:
        async def get(self, uid, cid):
            if uid == user_id and cid == conv_id:
                return state
            return None

    class FakeRunRepo:
        pass

    class FakeScoreRepo:
        pass

    svc = EvaluationService(
        run_repo=FakeRunRepo(),
        score_repo=FakeScoreRepo(),
        conversation_state_store=FakeStore(),
    )
    items = await svc.resolve_scope_items(
        "single",
        {"conversation_id": str(conv_id), "user_id": str(user_id), "turn_index": 0},
    )
    assert len(items) == 1
    assert items[0].turn.user_message == "Hello"
    assert items[0].turn.agent_response == "Hi there."


@pytest.mark.asyncio
async def test_execute_run_not_found():
    """execute_run does nothing when run is not found."""
    class FakeRunRepo:
        async def get_with_scores(self, id):
            return None

    class FakeScoreRepo:
        pass

    svc = EvaluationService(
        run_repo=FakeRunRepo(),
        score_repo=FakeScoreRepo(),
        conversation_state_store=None,
    )
    await svc.execute_run(uuid4())
    # No exception; nothing to do


@pytest.mark.asyncio
async def test_execute_run_skips_non_pending():
    """execute_run skips when run status is not pending."""
    run_id = uuid4()

    class FakeRunRepo:
        async def get_with_scores(self, id):
            r = type("Run", (), {"id": run_id, "status": "completed", "scope_type": "single", "scope_payload": {}, "judge_config_snapshot": {}})()
            return r

    class FakeScoreRepo:
        pass

    svc = EvaluationService(
        run_repo=FakeRunRepo(),
        score_repo=FakeScoreRepo(),
        conversation_state_store=None,
    )
    await svc.execute_run(run_id)
    # No exception; skips


@pytest.mark.asyncio
async def test_execute_run_empty_scope_sets_completed_with_error():
    """execute_run with no scope items marks run completed with error_message."""
    run_id = uuid4()
    updated = {}

    class FakeRunRepo:
        async def get_with_scores(self, id):
            return type("Run", (), {
                "id": run_id,
                "status": "pending",
                "scope_type": "single",
                "scope_payload": {"conversation_id": str(uuid4()), "user_id": str(uuid4())},
                "judge_config_snapshot": {"model": "gpt-4o-mini", "provider": "openai", "prompt_template": "x", "rubric": None},
            })()

        async def update(self, id, **kwargs):
            updated.update(kwargs)

    class FakeStore:
        async def get(self, uid, cid):
            return None

    class FakeScoreRepo:
        pass

    svc = EvaluationService(
        run_repo=FakeRunRepo(),
        score_repo=FakeScoreRepo(),
        conversation_state_store=FakeStore(),
    )
    await svc.execute_run(run_id)
    assert updated.get("status") == "completed"
    assert "No items" in (updated.get("error_message") or "")


@pytest.mark.asyncio
async def test_execute_run_calls_judge_and_persists_scores(judge_snapshot):
    """execute_run runs judge for each item and creates score records."""
    run_id = uuid4()
    conv_id = uuid4()
    runs_seen = []
    scores_created = []

    class FakeRunRepo:
        async def get_with_scores(self, id):
            r = type("Run", (), {
                "id": run_id,
                "status": "pending",
                "scope_type": "single",
                "scope_payload": {
                    "conversation_id": str(conv_id),
                    "inline": {"user_message": "Q", "agent_response": "A"},
                },
                "judge_config_snapshot": judge_snapshot,
            })()
            return r

        async def update(self, id, **kwargs):
            runs_seen.append(kwargs)

    class FakeScoreRepo:
        async def create(self, **kwargs):
            scores_created.append(kwargs)

    async def mock_run_judge(turn, config):
        return JudgeResult(scores={"accuracy": 4}, raw_output="{}", comment=None)

    svc = EvaluationService(
        run_repo=FakeRunRepo(),
        score_repo=FakeScoreRepo(),
        conversation_state_store=None,
    )
    # Patch run_judge so we don't call real LLM
    import apex.services.evaluation_service as evs
    original = evs.run_judge
    evs.run_judge = mock_run_judge
    try:
        await svc.execute_run(run_id)
    finally:
        evs.run_judge = original

    assert any(u.get("status") == "running" for u in runs_seen)
    assert any(u.get("status") == "completed" for u in runs_seen)
    assert len(scores_created) == 1
    assert scores_created[0]["run_id"] == run_id
    assert scores_created[0]["conversation_id"] == conv_id
    assert scores_created[0]["scores"] == {"accuracy": 4}
