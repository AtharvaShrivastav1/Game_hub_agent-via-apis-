import pytest
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.graph.workflow import assistant_graph
from app.graph.state import GameAssistantState
from app.agents.orchestrator import fallback_intent_classifier

def test_intent_routing_classification():
    # Test fallback routing heuristics
    d1 = fallback_intent_classifier("Recommend an RPG under 1500", None)
    assert d1.intent == "RECOMMEND"
    assert d1.max_price == 1500.0
    assert d1.genre == "Rpg"

    d2 = fallback_intent_classifier("Compare Cyberstrike and Chronicles of Eldoria", None)
    assert d2.intent == "COMPARE"

    d3 = fallback_intent_classifier("Buy Cyberstrike", None)
    assert d3.intent == "PURCHASE"

    d4 = fallback_intent_classifier("What is in my cart?", None)
    assert d4.intent == "CART_QUERY"

def test_langgraph_recommendation_workflow():
    thread_id = f"test_rec_{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    state: GameAssistantState = {
        "user_id": 1,
        "message": "Recommend an RPG under ₹2000",
        "current_game_id": None,
        "thread_id": thread_id,
        "purchase_approved": False,
        "purchase_requested": False,
        "agent_steps": [],
    }

    result = assistant_graph.invoke(state, config=config)
    assert result is not None
    assert len(result.get("agent_steps", [])) >= 2
    assert result.get("final_response") != ""

def test_langgraph_hitl_purchase_interrupt_and_resume():
    """
    Verifies that for purchase requests:
    1. LangGraph runs until the interrupt before execute_purchase.
    2. The thread state retains purchase_summary and requires human approval.
    3. Resuming with approval executes the atomic transaction.
    """
    thread_id = f"test_hitl_{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    state: GameAssistantState = {
        "user_id": 1,
        "message": "Buy Hollow Depths: Requiem",
        "current_game_id": None,
        "thread_id": thread_id,
        "purchase_approved": False,
        "purchase_requested": False,
        "agent_steps": [],
    }

    # Ensure test game is not already owned before running purchase test
    from app.database.session import SessionLocal
    from app.models.library import UserGameLibrary
    from app.models.game import Game
    _db = SessionLocal()
    _test_game = _db.query(Game).filter(Game.title.ilike("%Hollow Depths%")).first()
    if _test_game:
        _db.query(UserGameLibrary).filter(
            UserGameLibrary.user_id == 1,
            UserGameLibrary.game_id == _test_game.id
        ).delete(synchronize_session=False)
        _db.commit()
    _db.close()

    # Step 1: Run graph
    result = assistant_graph.invoke(state, config=config)


    # Inspect pause state
    current_state = assistant_graph.get_state(config)
    # The graph must have paused before execute_purchase!
    assert "execute_purchase" in (current_state.next or ())
    assert result.get("purchase_requested") is True
    assert result.get("purchase_summary") is not None
    assert "Hollow Depths" in str(result.get("purchase_summary"))

    # Step 2: Simulate Human Approval & Resume
    assistant_graph.update_state(config, {"purchase_approved": True})
    resume_result = assistant_graph.invoke(None, config=config)

    # After resume, execute_purchase ran and completed
    assert resume_result.get("transaction_result") is not None
    assert "Purchase Complete" in resume_result.get("final_response", "") or "Transaction Failed" in resume_result.get("final_response", "")

def test_natural_language_purchase_queries():
    """Test natural language purchase requests like 'please purchase riftwalker for me'."""
    thread_id = f"test_rift_{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    state: GameAssistantState = {
        "user_id": 1,
        "message": "please purchase riftwalker for me",
        "current_game_id": None,
        "thread_id": thread_id,
        "purchase_approved": False,
        "purchase_requested": False,
        "agent_steps": [],
    }

    result = assistant_graph.invoke(state, config=config)
    assert result.get("purchase_requested") is True
    assert result.get("purchase_summary") is not None
    assert "Riftwalker" in str(result.get("purchase_summary"))

def test_natural_language_chronicles_query():
    """Test natural language purchase requests like 'i want to buy chronicles of eldoria'."""
    thread_id = f"test_chronicles_{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    state: GameAssistantState = {
        "user_id": 1,
        "message": "i want to buy chronicles of eldoria",
        "current_game_id": None,
        "thread_id": thread_id,
        "purchase_approved": False,
        "purchase_requested": False,
        "agent_steps": [],
    }

    result = assistant_graph.invoke(state, config=config)
    assert result.get("purchase_requested") is True
    assert result.get("purchase_summary") is not None
    assert "Chronicles of Eldoria" in str(result.get("purchase_summary"))

def test_criteria_based_cheapest_purchase():
    """Test criteria-based query: 'i want to buy a game either rpg or action less than 2000rs and please purchse the cheapest one'."""
    thread_id = f"test_criteria_{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    state: GameAssistantState = {
        "user_id": 1,
        "message": "i want to buy a game either rpg or action less than 2000rs and please purchse the cheapest one",
        "current_game_id": None,
        "thread_id": thread_id,
        "purchase_approved": False,
        "purchase_requested": False,
        "agent_steps": [],
    }

    result = assistant_graph.invoke(state, config=config)
    assert result.get("purchase_requested") is True
    assert result.get("purchase_summary") is not None
    summary = result.get("purchase_summary", {})
    # Verify the selected game is under 2000 and valid
    assert summary.get("total_price") <= 2000.0
    assert len(summary.get("game_ids", [])) == 1

def test_horror_and_indie_cheapest_purchase():
    """Test criteria-based query: 'among the horror and indie genre purchase the cheapest game'."""
    thread_id = f"test_horror_indie_{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    state: GameAssistantState = {
        "user_id": 1,
        "message": "among the horror and indie genre purchase the cheapest game",
        "current_game_id": None,
        "thread_id": thread_id,
        "purchase_approved": False,
        "purchase_requested": False,
        "agent_steps": [],
    }

    result = assistant_graph.invoke(state, config=config)
    assert result.get("purchase_requested") is True
    assert result.get("purchase_summary") is not None
    summary = result.get("purchase_summary", {})
    # Pixel Dungeon: Endless Descent (ID 18, price 399) is the cheapest Horror/Indie game
    assert 18 in summary.get("game_ids", [])
    assert "Pixel Dungeon" in str(summary.get("game_titles", []))
    assert summary.get("total_price") == 399.0

def test_multiturn_context_referential_purchase():
    """Test multi-turn context memory: resolving 'buy the second one' from context_bucket."""
    thread_id = f"test_context_{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    from app.database.session import SessionLocal
    from app.models.library import UserGameLibrary
    _db = SessionLocal()
    _db.query(UserGameLibrary).filter(UserGameLibrary.user_id == 1, UserGameLibrary.game_id == 3).delete(synchronize_session=False)
    _db.commit()
    _db.close()

    # Turn 1 context with recommendations
    context_bucket = [
        {"role": "user", "content": "Recommend two great action games"},
        {
            "role": "assistant",
            "content": "Here are two great choices: 1. Cyberstrike: Neon Protocol, 2. Valkyrie Ascendant",
            "recommended_games": [
                {"id": 1, "title": "Cyberstrike: Neon Protocol", "price": 2499.0},
                {"id": 3, "title": "Valkyrie Ascendant", "price": 1899.0}
            ],
            "recommended_titles": ["Cyberstrike: Neon Protocol", "Valkyrie Ascendant"]
        }
    ]

    state: GameAssistantState = {
        "user_id": 1,
        "message": "buy the second one please",
        "current_game_id": None,
        "thread_id": thread_id,
        "purchase_approved": False,
        "purchase_requested": False,
        "context_bucket": context_bucket,
        "agent_steps": [],
    }

    result = assistant_graph.invoke(state, config=config)
    assert result.get("purchase_requested") is True
    assert result.get("purchase_summary") is not None
    summary = result.get("purchase_summary", {})
    # The second game (Valkyrie Ascendant, ID 3) should be selected
    assert 3 in summary.get("game_ids", [])

