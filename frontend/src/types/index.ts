export interface Game {
  id: number;
  title: string;
  description: string;
  genre: string;
  price: number;
  rating: number;
  duration_hours: number;
  developer: string;
  release_date: string;
  image_url: string;
  is_owned?: boolean;
  is_in_cart?: boolean;
}

export interface CartItem {
  id: number;
  user_id: number;
  game_id: number;
  quantity: number;
  created_at: string;
  game: Game;
}

export interface CartSummary {
  items: CartItem[];
  item_count: number;
  total_price: number;
  user_wallet_balance: number;
  is_affordable: boolean;
}

export interface User {
  id: number;
  name: string;
  email: string;
  wallet_balance: number;
}

export interface PurchaseSummary {
  game_ids: number[];
  game_titles: string[];
  total_price: number;
  current_wallet_balance: number;
  remaining_balance: number;
  can_afford: boolean;
  requires_approval: boolean;
}

export interface AgentStepLog {
  agent_name: string;
  action: string;
  details?: string;
}

export interface ChatResponse {
  thread_id: string;
  intent?: string;
  response: string;
  requires_approval: boolean;
  approval_data?: PurchaseSummary;
  agent_steps: AgentStepLog[];
  recommended_games: Partial<Game>[];
  cart_items: Partial<Game>[];
  transaction_result?: {
    success: boolean;
    message?: string;
    new_wallet_balance?: number;
    cancelled?: boolean;
    error?: string;
  };
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  thread_id?: string;
  requires_approval?: boolean;
  approval_data?: PurchaseSummary;
  agent_steps?: AgentStepLog[];
  recommended_games?: Partial<Game>[];
  transaction_result?: any;
  timestamp: string;
}
