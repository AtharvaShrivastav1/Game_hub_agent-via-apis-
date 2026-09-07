from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ChatRequest(BaseModel):
    user_id: int
    message: str
    current_game_id: Optional[int] = None
    thread_id: Optional[str] = None
    chat_history: Optional[List[Dict[str, Any]]] = None

class AgentStepLog(BaseModel):
    agent_name: str
    action: str
    details: Optional[str] = None

class ChatResponse(BaseModel):
    thread_id: str
    intent: Optional[str] = None
    response: str
    requires_approval: bool = False
    approval_data: Optional[Dict[str, Any]] = None
    agent_steps: List[AgentStepLog] = []
    recommended_games: List[Dict[str, Any]] = []
    cart_items: List[Dict[str, Any]] = []
    transaction_result: Optional[Dict[str, Any]] = None
    context_summary: Optional[Dict[str, Any]] = None
