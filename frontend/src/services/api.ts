import { Game, CartSummary, User, ChatResponse } from '../types';

const API_BASE = 'http://localhost:8000/api';

export const api = {
  // Games
  async getGames(params: {
    genre?: string;
    max_price?: number;
    max_duration?: number;
    min_rating?: number;
    search?: string;
    sort_by?: string;
    user_id?: number;
  } = {}): Promise<Game[]> {
    const query = new URLSearchParams();
    if (params.genre && params.genre !== 'All') query.set('genre', params.genre);
    if (params.max_price !== undefined) query.set('max_price', params.max_price.toString());
    if (params.max_duration !== undefined) query.set('max_duration', params.max_duration.toString());
    if (params.min_rating !== undefined) query.set('min_rating', params.min_rating.toString());
    if (params.search) query.set('search', params.search);
    if (params.sort_by) query.set('sort_by', params.sort_by);
    if (params.user_id) query.set('user_id', params.user_id.toString());

    const res = await fetch(`${API_BASE}/games?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch games');
    return res.json();
  },

  async getGenres(): Promise<string[]> {
    const res = await fetch(`${API_BASE}/games/genres`);
    if (!res.ok) return ['RPG', 'Action', 'Indie', 'Strategy', 'Horror', 'Simulation', 'Racing', 'Puzzle'];
    return res.json();
  },

  async getGame(gameId: number, userId?: number): Promise<Game> {
    const url = userId ? `${API_BASE}/games/${gameId}?user_id=${userId}` : `${API_BASE}/games/${gameId}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Game not found');
    return res.json();
  },

  // User
  async getUser(userId: number = 1): Promise<User> {
    const res = await fetch(`${API_BASE}/users/${userId}`);
    if (!res.ok) throw new Error('Failed to fetch user');
    return res.json();
  },

  async resetUserData(userId: number = 1): Promise<User> {
    const res = await fetch(`${API_BASE}/users/${userId}/reset`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to reset user data');
    return res.json();
  },

  async topupWallet(userId: number, amount: number): Promise<User> {

    const res = await fetch(`${API_BASE}/users/${userId}/wallet/topup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount }),
    });
    if (!res.ok) throw new Error('Failed to top up wallet');
    return res.json();
  },

  // Cart
  async getCart(userId: number = 1): Promise<CartSummary> {
    const res = await fetch(`${API_BASE}/users/${userId}/cart`);
    if (!res.ok) throw new Error('Failed to fetch cart');
    return res.json();
  },

  async addToCart(userId: number, gameId: number): Promise<CartSummary> {
    const res = await fetch(`${API_BASE}/users/${userId}/cart`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ game_id: gameId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to add game to cart');
    }
    return res.json();
  },

  async removeFromCart(userId: number, gameId: number): Promise<CartSummary> {
    const res = await fetch(`${API_BASE}/users/${userId}/cart/${gameId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to remove from cart');
    return res.json();
  },

  async clearCart(userId: number): Promise<CartSummary> {
    const res = await fetch(`${API_BASE}/users/${userId}/cart`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to clear cart');
    return res.json();
  },

  // Library
  async getLibrary(userId: number = 1): Promise<Game[]> {
    const res = await fetch(`${API_BASE}/users/${userId}/library`);
    if (!res.ok) throw new Error('Failed to fetch library');
    return res.json();
  },

  // AI Assistant & LangGraph
  async chatWithAssistant(
    userId: number,
    message: string,
    currentGameId?: number | null,
    threadId?: string | null
  ): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/assistant/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        message,
        current_game_id: currentGameId,
        thread_id: threadId,
      }),
    });
    if (!res.ok) throw new Error('Assistant query failed');
    return res.json();
  },

  // Human-in-the-loop purchase approval
  async approvePurchase(threadId: string): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/purchase/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        thread_id: threadId,
        approved: true,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Purchase approval execution failed');
    }
    return res.json();
  },

  async rejectPurchase(threadId: string): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/purchase/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        thread_id: threadId,
        approved: false,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Purchase rejection failed');
    }
    return res.json();
  },
};
