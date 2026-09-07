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
    genre: Optional[str] = Field(None, description="Primary extracted genre (e.g. RPG, Action, Indie, Strategy)")
    genres: List[str] = Field(default_factory=list, description="List of all extracted genres (e.g. ['RPG', 'Action'])")
    max_price: Optional[float] = Field(None, description="Maximum budget/price limit in rupees if mentioned")
    max_duration: Optional[float] = Field(None, description="Maximum completion time in hours if mentioned")
    min_rating: Optional[float] = Field(None, description="Minimum rating if mentioned")
    sort_preference: Optional[Literal["cheapest", "highest_rated", "shortest", "longest"]] = Field(None, description="Explicit sort/optimization preference (e.g. cheapest, best rated)")
    search_query: Optional[str] = Field(None, description="Specific search terms or game title mentioned")
    game_titles: List[str] = Field(default_factory=list, description="List of game titles explicitly mentioned")
    cart_action: Optional[Literal["add", "remove", "view"]] = Field(None, description="Action for cart if CART_MODIFICATION")

def fallback_intent_classifier(message: str, current_game_id: Optional[int], context_bucket: Optional[List[Dict[str, Any]]] = None) -> OrchestratorDecision:
    """Deterministic fallback classifier for resilient behavior."""
    msg = message.lower()

    # Price extraction: e.g. "under 1500", "under ₹1500", "budget 3000", "below 2000", "within 1000", "less than 500", "upto 2500"
    max_price = None
    price_match = re.search(r'(?:under|below|budget|within|max|less than|upto|up to)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)', msg)
    if not price_match:
        price_match = re.search(r'(?:₹|rs\.?|inr)\s*(\d+(?:\.\d+)?)', msg)
    if not price_match:
        price_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:₹|rs\.?|inr|rupees)', msg)
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

    # Genre extraction (extract all mentioned genres)
    known_genres = ["rpg", "action", "adventure", "strategy", "indie", "simulation", "racing", "horror", "puzzle", "rogue", "cyberpunk"]
    extracted_genres = []
    for g in known_genres:
        if re.search(r'\b' + re.escape(g) + r'\b', msg):
            extracted_genres.append(g.capitalize())
    primary_genre = extracted_genres[0] if extracted_genres else None

    # Sort preference extraction
    sort_pref = None
    if any(w in msg for w in ["cheapest", "lowest price", "least expensive", "most affordable", "cheap"]):
        sort_pref = "cheapest"
    elif any(w in msg for w in ["best rated", "highest rated", "top rated", "highest rating", "top rating"]):
        sort_pref = "highest_rated"
    elif any(w in msg for w in ["shortest", "quickest"]):
        sort_pref = "shortest"
    elif any(w in msg for w in ["longest"]):
        sort_pref = "longest"

    # Intent detection
    if any(w in msg for w in ["buy", "purchase", "purchse", "checkout", "place order"]):
        clean = re.sub(r'(?i)\b(?:please|pls|can you|could you|would you|i want to|i\'d like to|i would like to|i wanna|help me|buy|purchase|purchse|checkout|place order|order|get|acquire|for me|for my account|the game|a copy of|copy of|now|either|or|and|less than|under|below|rs|inr|rupees|the cheapest one|cheapest one|cheapest|the best one)\b', '', message).strip()
        clean = re.sub(r'^[^\w]+|[^\w]+$', '', clean).strip()

        # Check if remaining words are actual game titles or just criteria/stop words
        criteria_words = {
            "genre", "genres", "game", "games", "among", "between", "either", "or", "and",
            "the", "a", "an", "one", "ones", "of", "in", "cheapest", "cheap", "best",
            "rated", "rating", "highest", "lowest", "most", "least", "affordable", "expensive",
            "less", "more", "under", "below", "over", "above", "within", "upto", "up to",
            "budget", "price", "cost", "hours", "hrs", "duration", "playtime", "first", "second",
            "third", "last", "1st", "2nd", "3rd", "that"
        }
        remaining_words = [
            w.lower() for w in re.findall(r'\b\w+\b', clean)
            if w.lower() not in criteria_words
            and w.lower() not in [g.lower() for g in known_genres]
            and not re.match(r'^\d', w)
        ]
        titles = [clean] if remaining_words and len(clean) > 2 else []
        return OrchestratorDecision(
            intent="PURCHASE",
            max_price=max_price,
            max_duration=max_duration,
            genre=primary_genre,
            genres=extracted_genres,
            sort_preference=sort_pref,
            search_query=clean if remaining_words else None,
            game_titles=titles,
        )

    if any(w in msg for w in ["compare", "difference between", "versus", "vs"]):
        return OrchestratorDecision(
            intent="COMPARE",
            genre=primary_genre,
            genres=extracted_genres,
            max_price=max_price,
            sort_preference=sort_pref,
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
            genre=primary_genre,
            genres=extracted_genres,
            max_price=max_price,
            max_duration=max_duration,
            sort_preference=sort_pref,
        )

    if any(w in msg for w in ["find", "search", "games under", "show me"]):
        return OrchestratorDecision(
            intent="SEARCH",
            genre=primary_genre,
            genres=extracted_genres,
            max_price=max_price,
            max_duration=max_duration,
            sort_preference=sort_pref,
        )

    if current_game_id is not None:
        return OrchestratorDecision(
            intent="GENERAL_GAME_QUERY",
            search_query=message,
        )

    return OrchestratorDecision(
        intent="RECOMMEND",
        genre=primary_genre,
        genres=extracted_genres,
        max_price=max_price,
        max_duration=max_duration,
        sort_preference=sort_pref,
    )

def orchestrator_node(state: GameAssistantState) -> Dict[str, Any]:
    """LangGraph node: Orchestrator agent classifying user intent and constraints."""
    message = state.get("message", "")
    current_game_id = state.get("current_game_id")
    context_bucket = state.get("context_bucket", [])
    steps = list(state.get("agent_steps", []))

    # Format Context Bucket memory if present
    context_history_str = ""
    if context_bucket:
        formatted_turns = []
        for turn in context_bucket[-6:]:  # Keep recent 6 turns for prompt efficiency
            role = turn.get("role", "user").capitalize()
            content = turn.get("content", "")
            rec_titles = turn.get("recommended_titles", [])
            rec_str = f" [Recommended: {', '.join(rec_titles)}]" if rec_titles else ""
            formatted_turns.append(f"- {role}: {content}{rec_str}")
        context_history_str = "\nConversation Context Memory (Previous turns):\n" + "\n".join(formatted_turns) + "\n"

    # Fetch context of current game if present
    current_game_ctx = ""
    if current_game_id:
        game_info = get_game(current_game_id)
        if game_info:
            current_game_ctx = f"\nCurrently active game viewed on screen: '{game_info['title']}' (ID: {game_info['id']}, Genre: {game_info['genre']}, Price: ₹{game_info['price']})."

    decision: Optional[OrchestratorDecision] = None
    llm = get_llm()

    if llm:
        try:
            # Attempt structured output via with_structured_output
            structured_llm = llm.with_structured_output(OrchestratorDecision)
            prompt = (
                f"{ORCHESTRATOR_SYSTEM_PROMPT}\n"
                f"{context_history_str}"
                f"{current_game_ctx}\n"
                f"User Request: {message}\n"
                f"Analyze intent, multi-genre criteria, sorting preference (e.g. cheapest), referential game mentions, and constraints."
            )
            decision = structured_llm.invoke(prompt)
        except Exception as e:
            logger.warning(f"Structured LLM failed in orchestrator: {e}. Attempting JSON parsing...")
            try:
                raw_res = llm.invoke(
                    f"{ORCHESTRATOR_SYSTEM_PROMPT}\n"
                    f"{context_history_str}"
                    f"{current_game_ctx}\n"
                    f"User Request: {message}\n"
                    "Respond with a JSON object matching keys: intent, genre, genres, max_price, max_duration, min_rating, sort_preference, search_query, game_titles, cart_action."
                )
                content = stringify_content(raw_res.content if hasattr(raw_res, "content") else raw_res)
                # Clean code blocks
                clean = re.sub(r'```(?:json)?', '', content).strip()
                parsed = json.loads(clean)

                decision = OrchestratorDecision(**parsed)
            except Exception as e2:
                logger.warning(f"JSON parsing also failed: {e2}. Using deterministic classifier.")

    if not decision:
        decision = fallback_intent_classifier(message, current_game_id, context_bucket)

    steps.append({
        "agent_name": "Orchestrator Agent",
        "action": f"Classified intent as {decision.intent}",
        "details": f"Constraints: Genre={decision.genre or decision.genres}, MaxPrice={decision.max_price}, Sort={decision.sort_preference}"
    })

    requirements = {
        "genre": decision.genre,
        "genres": decision.genres or ([decision.genre] if decision.genre else []),
        "max_price": decision.max_price,
        "max_duration": decision.max_duration,
        "min_rating": decision.min_rating,
        "sort_preference": decision.sort_preference,
        "search_query": decision.search_query,
        "game_titles": decision.game_titles,
        "cart_action": decision.cart_action,
    }

    return {
        "intent": decision.intent,
        "requirements": requirements,
        "agent_steps": steps,
    }
