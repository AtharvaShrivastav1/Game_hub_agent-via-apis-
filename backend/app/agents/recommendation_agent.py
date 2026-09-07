import logging
from typing import Dict, Any, List
from app.graph.state import GameAssistantState
from app.prompts.recommendation_prompt import RECOMMENDATION_SYSTEM_PROMPT
from app.services.llm_factory import get_llm, stringify_content


logger = logging.getLogger(__name__)

def recommendation_agent_node(state: GameAssistantState) -> Dict[str, Any]:
    """LangGraph node: Recommendation Agent reasoning over retrieved candidate games."""
    message = state.get("message", "")
    intent = state.get("intent", "RECOMMEND")
    reqs = state.get("requirements", {})
    candidates = state.get("candidate_games", [])
    user_library = state.get("user_library", [])
    cart_items = state.get("cart_items", [])
    wallet_info = state.get("wallet_info", {})
    steps = list(state.get("agent_steps", []))

    # Filter out already owned games for recommendations
    owned_ids = {item["game_id"] for item in user_library}
    unowned_candidates = [c for c in candidates if c.get("id") not in owned_ids]

    budget = reqs.get("max_price")
    max_duration = reqs.get("max_duration")
    genre = reqs.get("genre")

    context_bucket = state.get("context_bucket", [])
    context_history_str = ""
    if context_bucket:
        formatted_turns = []
        for turn in context_bucket[-6:]:
            role = turn.get("role", "user").capitalize()
            content = turn.get("content", "")
            rec_titles = turn.get("recommended_titles", [])
            rec_str = f" [Recommended: {', '.join(rec_titles)}]" if rec_titles else ""
            formatted_turns.append(f"- {role}: {content}{rec_str}")
        context_history_str = "\nConversation Context Memory (Previous turns):\n" + "\n".join(formatted_turns) + "\n"

    llm = get_llm()
    final_text = ""
    top_recommendations: List[Dict[str, Any]] = []

    if llm:
        try:
            candidates_summary = "\n".join([
                f"- ID {c.get('id')}: {c.get('title')} | Genre: {c.get('genre')} | Price: ₹{c.get('price')} | Rating: {c.get('rating')} | Playtime: {c.get('duration_hours')} hrs | Owned: {c.get('id') in owned_ids}"
                for c in candidates[:8]
            ])
            user_owned_summary = ", ".join([item["title"] for item in user_library]) if user_library else "None"
            user_cart_summary = ", ".join([item["title"] for item in cart_items]) if cart_items else "Empty"

            prompt = (
                f"{RECOMMENDATION_SYSTEM_PROMPT}\n\n"
                f"{context_history_str}\n"
                f"User Intent: {intent}\n"
                f"User Message: {message}\n"
                f"User Wallet Balance: ₹{wallet_info.get('wallet_balance', 0):.2f}\n"
                f"User Owned Games: {user_owned_summary}\n"
                f"User Cart: {user_cart_summary}\n\n"
                f"Grounded Candidate Games Available in GameHub Catalog:\n{candidates_summary}\n\n"
                "Provide a clear, engaging, and structured response addressing the user's request. "
                "Include the game names, why they fit, and clear recommendations without hallucinating unlisted titles."
            )
            response = llm.invoke(prompt)
            raw_content = response.content if hasattr(response, "content") else response
            final_text = stringify_content(raw_content)
        except Exception as e:
            logger.warning(f"LLM call failed in recommendation agent: {e}. Falling back to rule-based response.")


    # Rule-based fallback if LLM is unavailable or failed
    if not final_text:
        if intent == "COMPARE":
            if len(candidates) >= 2:
                g1, g2 = candidates[0], candidates[1]
                final_text = (
                    f"### Comparison: **{g1['title']}** vs **{g2['title']}**\n\n"
                    f"| Attribute | {g1['title']} | {g2['title']} |\n"
                    f"|---|---|---|\n"
                    f"| **Genre** | {g1['genre']} | {g2['genre']} |\n"
                    f"| **Price** | ₹{g1['price']:.2f} | ₹{g2['price']:.2f} |\n"
                    f"| **Rating** | ⭐ {g1['rating']}/5.0 | ⭐ {g2['rating']}/5.0 |\n"
                    f"| **Playtime** | {g1['duration_hours']} hours | {g2['duration_hours']} hours |\n\n"
                    f"- **{g1['title']}** offers deep immersion with {g1['duration_hours']} hours of gameplay at ₹{g1['price']}.\n"
                    f"- **{g2['title']}** is rated {g2['rating']}/5.0 and is a great alternative in the {g2['genre']} category."
                )
            else:
                final_text = "I need at least two candidate games to formulate an in-depth comparison. Please specify the games you would like to compare."

        elif intent == "GENERAL_GAME_QUERY" and state.get("current_game_id"):
            cg = next((c for c in candidates if c.get("id") == state.get("current_game_id")), None)
            if cg:
                value_rating = "exceptional" if cg['rating'] >= 4.5 else "solid"
                final_text = (
                    f"### Is **{cg['title']}** worth buying?\n\n"
                    f"**Verdict:** Yes! It is an {value_rating} purchase at **₹{cg['price']}**.\n\n"
                    f"- **Genre:** {cg['genre']}\n"
                    f"- **Player Rating:** ⭐ {cg['rating']} / 5.0\n"
                    f"- **Estimated Playtime:** ~{cg['duration_hours']} hours\n"
                    f"- **Value Ratio:** Approximately ₹{cg['price']/max(cg['duration_hours'], 1):.1f} per hour of entertainment.\n\n"
                    f"*{cg['description']}*"
                )
            else:
                final_text = "The game you are viewing looks like a solid choice based on player feedback!"

        elif intent in ["CART_QUERY", "CART_MODIFICATION"]:
            if cart_items:
                total = sum(item["price"] for item in cart_items)
                items_str = "\n".join([f"- **{item['title']}** — ₹{item['price']}" for item in cart_items])
                final_text = (
                    f"Here is what's currently in your cart:\n{items_str}\n\n"
                    f"**Total:** ₹{total:.2f} | **Available Wallet:** ₹{wallet_info.get('wallet_balance', 0):.2f}\n"
                    f"{'You have enough funds to complete this purchase!' if wallet_info.get('wallet_balance', 0) >= total else 'You may need to top up your wallet before checkout.'}"
                )
            else:
                final_text = "Your cart is currently empty! Explore the catalog to discover exciting games."

        else:
            # Standard recommendations
            target_list = unowned_candidates if unowned_candidates else candidates
            selected = target_list[:2]
            recs_text = []
            for g in selected:
                recs_text.append(
                    f"- **{g['title']}** (₹{g['price']}) — {g['genre']} | ⭐ {g['rating']}/5.0 | ~{g['duration_hours']}h\n  *{g['description']}*"
                )
            final_text = (
                f"Based on your request, here are top recommended games from GameHub:\n\n"
                + "\n\n".join(recs_text)
            )

    top_recommendations = unowned_candidates[:4] if unowned_candidates else candidates[:4]

    steps.append({
        "agent_name": "Recommendation Agent",
        "action": f"Formulated recommendations/insights for intent {intent}",
        "details": f"Generated reasoning over {len(candidates)} grounded games."
    })

    return {
        "final_response": final_text,
        "recommendations": top_recommendations,
        "agent_steps": steps,
    }
