import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.graph.state import GameAssistantState
from app.prompts.purchase_prompt import PURCHASE_SYSTEM_PROMPT
from app.services.llm_factory import get_llm, stringify_content
from app.tools.game_tools import (
    search_games,
    get_game,
    get_user_cart,
    get_user_library,
    get_user_wallet,
    validate_purchase,
)

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "a", "an", "the", "and", "or", "for", "of", "to", "in", "on", "at", "by", "from",
    "with", "is", "it", "this", "that", "these", "those", "among", "between", "either",
    "neither", "game", "games", "genre", "genres", "cheap", "cheapest", "expensive",
    "best", "top", "rated", "rating", "highest", "lowest", "most", "least", "buy",
    "purchase", "purchse", "order", "get", "want", "like", "need", "please", "pls",
    "can", "could", "would", "you", "me", "my", "i", "we", "one", "ones", "less",
    "more", "under", "over", "below", "above", "within", "price", "budget", "cost",
    "rs", "inr", "rupee", "rupees", "now", "first", "second", "third", "last",
    "1st", "2nd", "3rd", "that"
}


class PurchaseAgentDecision(BaseModel):
    is_cart_checkout: bool = Field(
        False,
        description="True if the user intends to purchase/checkout all items currently in their shopping cart."
    )
    selected_game_ids: List[int] = Field(
        default_factory=list,
        description="List of integer game IDs from the available catalog that match the user's purchase request or criteria."
    )
    reasoning: str = Field(
        "",
        description="Clear, natural reasoning explaining which game(s) were chosen and how they satisfy the user's constraints."
    )


def fallback_purchase_resolver(
    message: str,
    requirements: Dict[str, Any],
    all_catalog_games: List[Dict[str, Any]],
    context_bucket: List[Dict[str, Any]],
    user_id: int,
) -> Tuple[List[int], str, bool]:
    """
    Emergency deterministic circuit breaker.
    Executes ONLY when LLM APIs are unreachable, time out, or fail to produce valid output.
    Returns: (game_ids_to_buy, criteria_selection_note, is_empty_cart_error)
    """
    msg = message.lower()
    game_ids_to_buy: List[int] = []
    criteria_selection_note = ""

    # 1. Cart Purchase
    if any(w in msg for w in ["cart", "everything in my cart", "checkout cart", "buy cart"]):
        cart_info = get_user_cart(user_id)
        game_ids_to_buy = [item["game_id"] for item in cart_info.get("items", [])]
        if not game_ids_to_buy:
            return [], "", True
        return game_ids_to_buy, "Selected all items currently in your shopping cart.", False

    # 2. Context-bucket referential resolution (e.g. "buy the second one")
    if not game_ids_to_buy and context_bucket:
        recent_recs = []
        for turn in reversed(context_bucket):
            if turn.get("recommended_games"):
                recent_recs = turn["recommended_games"]
                break
            elif turn.get("recommended_ids"):
                recent_recs = [{"id": gid, "title": f"Game {gid}"} for gid in turn["recommended_ids"]]
                break

        if recent_recs:
            if re.search(r'\b(?:first|1st|first one|1st one)\b', msg):
                game_ids_to_buy = [recent_recs[0]["id"]]
                criteria_selection_note = f"Selected the 1st game from previous recommendations (**{recent_recs[0].get('title', 'Game')}**)."
            elif len(recent_recs) >= 2 and re.search(r'\b(?:second|2nd|second one|2nd one)\b', msg):
                game_ids_to_buy = [recent_recs[1]["id"]]
                criteria_selection_note = f"Selected the 2nd game from previous recommendations (**{recent_recs[1].get('title', 'Game')}**)."
            elif len(recent_recs) >= 3 and re.search(r'\b(?:third|3rd|third one|3rd one)\b', msg):
                game_ids_to_buy = [recent_recs[2]["id"]]
                criteria_selection_note = f"Selected the 3rd game from previous recommendations (**{recent_recs[2].get('title', 'Game')}**)."
            elif re.search(r'\b(?:last|last one)\b', msg):
                game_ids_to_buy = [recent_recs[-1]["id"]]
                criteria_selection_note = f"Selected the last game from previous recommendations (**{recent_recs[-1].get('title', 'Game')}**)."

    # 3. Explicit Game Title Mentioned
    if not game_ids_to_buy:
        req_titles = requirements.get("game_titles", [])
        for req_t in req_titles:
            if req_t and len(req_t.strip()) > 1:
                matched = search_games(search=req_t.strip(), limit=3)
                if matched:
                    for m in matched:
                        if m["id"] not in game_ids_to_buy:
                            game_ids_to_buy.append(m["id"])
                    break

        if not game_ids_to_buy:
            best_matches = []
            for g in all_catalog_games:
                title_lower = g["title"].lower()
                base_title = re.split(r'[:\-\(]', title_lower)[0].strip()
                if title_lower in msg:
                    best_matches.append((len(title_lower), g["id"]))
                elif len(base_title) >= 3 and re.search(r'\b' + re.escape(base_title) + r'\b', msg):
                    best_matches.append((len(base_title), g["id"]))

            if best_matches:
                best_matches.sort(key=lambda x: x[0], reverse=True)
                game_ids_to_buy.append(best_matches[0][1])

    # 4. Criteria-based auto-selection
    if not game_ids_to_buy:
        genres = [g.lower() for g in requirements.get("genres", [])]
        if not genres and requirements.get("genre"):
            genres = [requirements["genre"].lower()]
        max_price = requirements.get("max_price")
        max_duration = requirements.get("max_duration")
        min_rating = requirements.get("min_rating")
        sort_pref = requirements.get("sort_preference") or ("cheapest" if "cheapest" in msg else None)

        if genres or max_price is not None or sort_pref:
            user_lib = get_user_library(user_id)
            owned_ids = {item["game_id"] for item in user_lib}
            candidates = [g for g in all_catalog_games if g["id"] not in owned_ids]

            if genres:
                candidates = [
                    g for g in candidates
                    if any(req_g in g["genre"].lower() for req_g in genres)
                ]
            if max_price is not None:
                candidates = [g for g in candidates if g["price"] <= max_price]
            if max_duration is not None:
                candidates = [g for g in candidates if g["duration_hours"] <= max_duration]
            if min_rating is not None:
                candidates = [g for g in candidates if g["rating"] >= min_rating]

            if candidates:
                if sort_pref == "cheapest":
                    candidates.sort(key=lambda x: x["price"])
                elif sort_pref == "highest_rated":
                    candidates.sort(key=lambda x: x["rating"], reverse=True)
                elif sort_pref == "shortest":
                    candidates.sort(key=lambda x: x["duration_hours"])
                elif sort_pref == "longest":
                    candidates.sort(key=lambda x: x["duration_hours"], reverse=True)
                else:
                    candidates.sort(key=lambda x: x["rating"] / (x["price"] + 1), reverse=True)

                chosen = candidates[0]
                game_ids_to_buy = [chosen["id"]]
                genres_label = "/".join([g.capitalize() for g in genres]) if genres else "Catalog"
                criteria_selection_note = (
                    f"Selected **{chosen['title']}** based on your criteria "
                    f"({genres_label}" + (f", under ₹{max_price:.0f}" if max_price else "") +
                    (f", sorted by {sort_pref}" if sort_pref else "") + ")."
                )

    # 5. Fuzzy search on non-stop words
    if not game_ids_to_buy:
        query = requirements.get("search_query") or message
        clean_query = re.sub(
            r'(?i)\b(?:please|pls|can you|could you|would you|i want to|i\'d like to|i would like to|i wanna|help me|buy|purchase|get|order|checkout|acquire|pay for|the game|a copy of|copy of|for me|for my account|now|immediately)\b',
            '',
            query
        ).strip()
        clean_query = re.sub(r'^[^\w]+|[^\w]+$', '', clean_query).strip()

        if clean_query:
            sig_words = [
                w for w in clean_query.split()
                if len(w) > 2 and w.lower() not in STOP_WORDS and not re.match(r'^\d', w)
            ]
            for w in sig_words:
                matched = search_games(search=w, limit=3)
                if matched:
                    game_ids_to_buy.append(matched[0]["id"])
                    break

    return game_ids_to_buy, criteria_selection_note, False


def purchase_agent_node(state: GameAssistantState) -> Dict[str, Any]:
    """
    LangGraph node: LLM-First Purchase / Validation Agent.
    
    Primary path: Uses Google Gemini with structured output to naturally analyze
    the user's intent, compound constraints, ordinal references, and catalog candidates.
    
    Secondary path: Quarantined deterministic fallback circuit breaker that engages
    ONLY if the LLM API is unavailable, times out, or fails to return valid output.
    """
    user_id = state.get("user_id", 1)
    message = state.get("message", "")
    current_game_id = state.get("current_game_id")
    context_bucket = state.get("context_bucket", [])
    requirements = state.get("requirements", {})
    steps = list(state.get("agent_steps", []))

    # Fetch factual data via backend tools
    all_catalog_games = search_games(limit=100)
    user_lib = get_user_library(user_id)
    owned_ids = {item["game_id"] for item in user_lib}
    wallet_info = get_user_wallet(user_id)
    cart_info = get_user_cart(user_id)
    cart_items = cart_info.get("items", [])

    # Filter unowned games for purchasing candidates
    unowned_candidates = [g for g in all_catalog_games if g["id"] not in owned_ids]

    game_ids_to_buy: List[int] = []
    criteria_selection_note = ""
    decision: Optional[PurchaseAgentDecision] = None

    # =========================================================================
    # PRIMARY PATH: LLM Natural Reasoning
    # =========================================================================
    llm = get_llm()
    if llm:
        try:
            # Build structured context history
            context_history_str = ""
            if context_bucket:
                formatted_turns = []
                for turn in context_bucket[-6:]:
                    role = turn.get("role", "user").capitalize()
                    content = turn.get("content", "")
                    rec_games = turn.get("recommended_games", [])
                    rec_titles = turn.get("recommended_titles", [])
                    if rec_games:
                        rec_str = " [Recommended: " + ", ".join([f"ID {rg.get('id')}: {rg.get('title')}" for rg in rec_games]) + "]"
                    elif rec_titles:
                        rec_str = f" [Recommended: {', '.join(rec_titles)}]"
                    else:
                        rec_str = ""
                    formatted_turns.append(f"- {role}: {content}{rec_str}")
                context_history_str = "\nConversation Context Memory (Previous turns):\n" + "\n".join(formatted_turns) + "\n"

            # Format unowned catalog candidates
            candidates_str = "\n".join([
                f"- ID {g['id']}: {g['title']} | Genre: {g['genre']} | Price: ₹{g['price']:.2f} | Rating: {g['rating']} | Playtime: {g['duration_hours']} hrs"
                for g in unowned_candidates
            ])

            cart_str = ", ".join([f"ID {item['game_id']}: {item['title']}" for item in cart_items]) if cart_items else "Empty"

            prompt = (
                f"{PURCHASE_SYSTEM_PROMPT}\n\n"
                f"{context_history_str}"
                f"User Request: {message}\n"
                f"User Wallet Balance: ₹{wallet_info.get('wallet_balance', 0):.2f}\n"
                f"User Current Cart: {cart_str}\n\n"
                f"Available Unowned Catalog Games:\n{candidates_str}\n\n"
                "Instructions:\n"
                "- If the user wants to buy their cart items, set is_cart_checkout = true.\n"
                "- If the user specifies criteria (e.g. 'among horror and indie buy the cheapest', 'an RPG under 2000'), "
                "reason across the candidate list and select the exact matching game ID(s).\n"
                "- If the user refers to a previous turn (e.g. 'buy the second one'), resolve it using Conversation Context Memory.\n"
                "- Set selected_game_ids with the chosen IDs and provide brief natural reasoning."
            )

            try:
                structured_llm = llm.with_structured_output(PurchaseAgentDecision)
                decision = structured_llm.invoke(prompt)
            except Exception as e_struct:
                logger.info(f"Structured output failed in purchase agent: {e_struct}. Attempting JSON parsing...")
                raw_res = llm.invoke(
                    f"{prompt}\n\nRespond with a valid JSON object matching keys: is_cart_checkout (bool), selected_game_ids (list of ints), reasoning (str)."
                )
                content = stringify_content(raw_res.content if hasattr(raw_res, "content") else raw_res)
                clean = re.sub(r'```(?:json)?', '', content).strip()
                parsed = json.loads(clean)
                decision = PurchaseAgentDecision(**parsed)

            if decision:
                if decision.is_cart_checkout:
                    game_ids_to_buy = [item["game_id"] for item in cart_items]
                    if not game_ids_to_buy:
                        return {
                            "final_response": "Your cart is currently empty. Add some games to your cart before proceeding to purchase!",
                            "purchase_requested": False,
                            "agent_steps": steps + [{
                                "agent_name": "Purchase Agent",
                                "action": "Validated purchase request (LLM Reasoning)",
                                "details": "Cart was empty, aborted purchase workflow."
                            }],
                        }
                    criteria_selection_note = "Selected all items currently in your shopping cart."
                elif decision.selected_game_ids:
                    # Validate that selected IDs exist in catalog
                    valid_catalog_ids = {g["id"] for g in all_catalog_games}
                    game_ids_to_buy = [gid for gid in decision.selected_game_ids if gid in valid_catalog_ids]
                    criteria_selection_note = decision.reasoning

        except Exception as e_llm:
            logger.warning(
                f"Primary LLM reasoning failed in Purchase Agent: {e_llm}. "
                "Engaging emergency deterministic circuit breaker..."
            )

    # =========================================================================
    # SECONDARY PATH: Emergency Deterministic Circuit Breaker
    # =========================================================================
    if not game_ids_to_buy:
        fb_ids, fb_note, is_empty_cart = fallback_purchase_resolver(
            message=message,
            requirements=requirements,
            all_catalog_games=all_catalog_games,
            context_bucket=context_bucket,
            user_id=user_id,
        )
        if is_empty_cart:
            return {
                "final_response": "Your cart is currently empty. Add some games to your cart before proceeding to purchase!",
                "purchase_requested": False,
                "agent_steps": steps + [{
                    "agent_name": "Purchase Agent",
                    "action": "Validated purchase request (Fallback Circuit Breaker)",
                    "details": "Cart was empty, aborted purchase workflow."
                }],
            }
        if fb_ids:
            game_ids_to_buy = fb_ids
            criteria_selection_note = fb_note

    # If neither LLM nor circuit breaker could identify games
    if not game_ids_to_buy:
        return {
            "final_response": "I could not identify which game you would like to purchase. Please specify a game title, criteria (e.g. 'cheapest RPG under ₹2000'), or say 'Buy everything in my cart'.",
            "purchase_requested": False,
            "agent_steps": steps + [{
                "agent_name": "Purchase Agent",
                "action": "Game identification failed",
                "details": "No matching game could be resolved from request or criteria."
            }],
        }

    # =========================================================================
    # PURCHASE VALIDATION VIA BACKEND API
    # =========================================================================
    val = validate_purchase(user_id, game_ids_to_buy)

    if not val.get("valid"):
        error_msg = val.get("error", "Purchase validation failed.")
        return {
            "final_response": f"Purchase Validation Notice: {error_msg}",
            "purchase_requested": False,
            "error": error_msg,
            "agent_steps": steps + [{
                "agent_name": "Purchase Agent",
                "action": "Purchase pre-validation failed",
                "details": error_msg
            }],
        }

    # Validation succeeded: Prepare purchase summary for human confirmation
    summary = {
        "game_ids": val["game_ids"],
        "game_titles": val["game_titles"],
        "total_price": val["total_price"],
        "current_wallet_balance": val["current_wallet_balance"],
        "remaining_balance": val["remaining_balance"],
        "can_afford": val["can_afford"],
        "requires_approval": True,
    }

    titles_str = ", ".join(val["game_titles"])
    note_header = f"\n*{criteria_selection_note}*\n" if criteria_selection_note else ""
    response_msg = (
        f"### Purchase Confirmation Required\n{note_header}\n"
        f"You are about to purchase: **{titles_str}**\n\n"
        f"- **Total Price:** ₹{val['total_price']:.2f}\n"
        f"- **Current Wallet Balance:** ₹{val['current_wallet_balance']:.2f}\n"
        f"- **Remaining Balance:** ₹{val['remaining_balance']:.2f}\n\n"
        f"Do you want to proceed with this purchase? Please review and confirm below."
    )

    steps.append({
        "agent_name": "Purchase Agent",
        "action": "Validated purchase conditions and prepared approval summary",
        "details": f"Games: {titles_str} | Total: ₹{val['total_price']:.2f} | Affordable: {val['can_afford']}"
    })

    return {
        "purchase_requested": True,
        "purchase_approved": False,
        "purchase_summary": summary,
        "final_response": response_msg,
        "agent_steps": steps,
    }
