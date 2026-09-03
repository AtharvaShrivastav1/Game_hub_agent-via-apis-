import json
import re
import logging
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from app.graph.state import GameAssistantState
from app.prompts.orchestrator_prompt import ORCHESTRATOR_SYSTEM_PROMPT
from app.services.llm_factory import get_llm, stringify_content
from app.tools.game_tools import get_game


logger = logging.getLogger(__name__)

class OrchestratorDecision(BaseModel):
    intent: Literal[
        "SEARCH",
        "RECOMMEND",
        "COMPARE",
        "CART_QUERY",
        "CART_MODIFICATION",
        "PURCHASE",
        "GENERAL_GAME_QUERY",
    ] = Field(description="The classified intent of the user")
    genre: Optional[str] = Field(None, description="Extracted genre (e.g. RPG, Action, Indie, Strategy)")
    max_price: Optional[float] = Field(None, description="Maximum budget/price limit in rupees if mentioned")
    max_duration: Optional[float] = Field(None, description="Maximum completion time in hours if mentioned")
    min_rating: Optional[float] = Field(None, description="Minimum rating if mentioned")
    search_query: Optional[str] = Field(None, description="Specific search terms or game title mentioned")
    game_titles: List[str] = Field(default_factory=list, description="List of game titles explicitly mentioned")
    cart_action: Optional[Literal["add", "remove", "view"]] = Field(None, description="Action for cart if CART_MODIFICATION")

def fallback_intent_classifier(message: str, current_game_id: Optional[int]) -> OrchestratorDecision:
    """Deterministic fallback classifier for resilient behavior."""
    msg = message.lower()

    # Price extraction: e.g. "under 1500", "under ₹1500", "budget 3000"
    max_price = None
    price_match = re.search(r'(?:under|below|budget|within|max)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)', msg)
    if not price_match:
        price_match = re.search(r'(?:₹|rs\.?|inr)\s*(\d+(?:\.\d+)?)', msg)
    if price_match:
        try:
            max_price = float(price_match.group(1))
        except ValueError:
            pass

    # Duration extraction: e.g. "under 20 hours", "under 30 hrs"
    max_duration = None
    duration_match = re.search(r'(?:under|below|within|less than)\s*(\d+)\s*(?:hours?|hrs?)', msg)
    if duration_match:
        try:
            max_duration = float(duration_match.group(1))
        except ValueError:
            pass

    # Genre extraction
    genres = ["rpg", "action", "adventure", "strategy", "indie", "simulation", "racing", "horror", "puzzle", "rogue", "cyberpunk"]
    extracted_genre = None
    for g in genres:
        if g in msg:
            extracted_genre = g.capitalize()
            break

    # Intent detection
    if any(w in msg for w in ["buy", "purchase", "checkout", "place order"]):
        return OrchestratorDecision(
            intent="PURCHASE",
            max_price=max_price,
            max_duration=max_duration,
            genre=extracted_genre,
            search_query=message,
        )

    if any(w in msg for w in ["compare", "difference between", "versus", "vs"]):
        return OrchestratorDecision(
            intent="COMPARE",
            genre=extracted_genre,
            max_price=max_price,
            search_query=message,
        )

    if any(w in msg for w in ["add to cart", "put in cart", "remove from cart", "drop from cart"]):
        action = "remove" if "remove" in msg or "drop" in msg else "add"
        return OrchestratorDecision(
            intent="CART_MODIFICATION",
            cart_action=action,
            search_query=message,
        )

    if any(w in msg for w in ["what's in my cart", "what is in my cart", "my cart", "cart contents", "in my cart"]):
        return OrchestratorDecision(
            intent="CART_QUERY",
            max_price=max_price,
        )

    if any(w in msg for w in ["recommend", "suggest", "what should i buy", "best game", "pick for me"]):
        return OrchestratorDecision(
            intent="RECOMMEND",
            genre=extracted_genre,
            max_price=max_price,
            max_duration=max_duration,
        )

    if any(w in msg for w in ["find", "search", "games under", "show me"]):
        return OrchestratorDecision(
            intent="SEARCH",
            genre=extracted_genre,
            max_price=max_price,
            max_duration=max_duration,
        )

    if current_game_id is not None:
        return OrchestratorDecision(
            intent="GENERAL_GAME_QUERY",
            search_query=message,
        )

    return OrchestratorDecision(
        intent="RECOMMEND",
        genre=extracted_genre,
        max_price=max_price,
        max_duration=max_duration,
    )

def orchestrator_node(state: GameAssistantState) -> Dict[str, Any]:
    """LangGraph node: Orchestrator agent classifying user intent and constraints."""
    message = state.get("message", "")
    current_game_id = state.get("current_game_id")
    steps = list(state.get("agent_steps", []))

    # Fetch context of current game if present
    current_game_ctx = ""
    if current_game_id:
        game_info = get_game(current_game_id)
        if game_info:
            current_game_ctx = f"\nCurrently active game viewed: '{game_info['title']}' (ID: {game_info['id']}, Genre: {game_info['genre']}, Price: ₹{game_info['price']})."

    decision: Optional[OrchestratorDecision] = None
    llm = get_llm()

    if llm:
        try:
            # Attempt structured output via with_structured_output
            structured_llm = llm.with_structured_output(OrchestratorDecision)
            prompt = (
                f"{ORCHESTRATOR_SYSTEM_PROMPT}\n"
                f"{current_game_ctx}\n"
                f"User Request: {message}\n"
                f"Analyze intent and constraints."
            )
            decision = structured_llm.invoke(prompt)
        except Exception as e:
            logger.warning(f"Structured LLM failed in orchestrator: {e}. Attempting JSON parsing...")
            try:
                raw_res = llm.invoke(
                    f"{ORCHESTRATOR_SYSTEM_PROMPT}\n"
                    f"{current_game_ctx}\n"
                    f"User Request: {message}\n"
                    "Respond with a JSON object matching keys: intent, genre, max_price, max_duration, min_rating, search_query, game_titles, cart_action."
                )
                content = stringify_content(raw_res.content if hasattr(raw_res, "content") else raw_res)
                # Clean code blocks
                clean = re.sub(r'```(?:json)?', '', content).strip()
                parsed = json.loads(clean)

                decision = OrchestratorDecision(**parsed)
            except Exception as e2:
                logger.warning(f"JSON parsing also failed: {e2}. Using deterministic classifier.")

    if not decision:
        decision = fallback_intent_classifier(message, current_game_id)

    steps.append({
        "agent_name": "Orchestrator Agent",
        "action": f"Classified intent as {decision.intent}",
        "details": f"Constraints: Genre={decision.genre}, MaxPrice={decision.max_price}, MaxDuration={decision.max_duration}"
    })

    requirements = {
        "genre": decision.genre,
        "max_price": decision.max_price,
        "max_duration": decision.max_duration,
        "min_rating": decision.min_rating,
        "search_query": decision.search_query,
        "game_titles": decision.game_titles,
        "cart_action": decision.cart_action,
    }

    return {
        "intent": decision.intent,
        "requirements": requirements,
        "agent_steps": steps,
    }
