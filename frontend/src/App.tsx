import React, { useState, useEffect } from 'react';
import { Game, CartSummary, User, ChatMessage, PurchaseSummary } from './types';
import { api } from './services/api';
import { Navbar } from './components/Navbar';
import { DiscoverPage } from './pages/DiscoverPage';
import { GameDetailsPage } from './pages/GameDetailsPage';
import { CartPage } from './pages/CartPage';
import { LibraryPage } from './pages/LibraryPage';
import { CategoriesPage } from './pages/CategoriesPage';
import { AssistantDrawer } from './components/AssistantDrawer';
import { TopupModal } from './components/TopupModal';
import { PurchaseApprovalModal } from './components/PurchaseApprovalModal';
import { Toast, ToastMessage } from './components/Toast';

export const App: React.FC = () => {
  // Navigation & View State
  const [activeTab, setActiveTab] = useState<'discover' | 'categories' | 'library' | 'cart'>('discover');
  const [selectedGame, setSelectedGame] = useState<Game | null>(null);

  // Application Data
  const [user, setUser] = useState<User | null>(null);
  const [games, setGames] = useState<Game[]>([]);
  const [genres, setGenres] = useState<string[]>([]);
  const [cart, setCart] = useState<CartSummary | null>(null);
  const [library, setLibrary] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);

  // Filter States
  const [selectedGenre, setSelectedGenre] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [maxPrice, setMaxPrice] = useState<number | null>(null);
  const [maxDuration, setMaxDuration] = useState<number | null>(null);
  const [sortBy, setSortBy] = useState('rating_desc');

  // AI Assistant State
  const [isAssistantOpen, setIsAssistantOpen] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome_1',
      sender: 'assistant',
      text: "👋 Welcome to **GameHub**! I am your AI Game Store Assistant powered by **LangGraph multi-agent orchestration**.\n\nI can search games, evaluate playtimes, compare titles, build custom budget combinations, and manage purchases with human approval.",
      timestamp: new Date().toLocaleTimeString(),
    }
  ]);

  // Modal States
  const [isTopupOpen, setIsTopupOpen] = useState(false);
  const [approvalModalOpen, setApprovalModalOpen] = useState(false);
  const [approvalSummary, setApprovalSummary] = useState<PurchaseSummary | null>(null);
  const [approvalThreadId, setApprovalThreadId] = useState<string | null>(null);
  const [approvalLoading, setApprovalLoading] = useState(false);

  // Toast notifications
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = (type: 'success' | 'error' | 'info', text: string) => {
    const id = Date.now().toString() + Math.random().toString(36).slice(2, 7);
    setToasts((prev) => [...prev, { id, type, text }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Initial Data Fetching
  const refreshUserData = async () => {
    try {
      const u = await api.getUser(1);
      setUser(u);
      const c = await api.getCart(1);
      setCart(c);
      const lib = await api.getLibrary(1);
      setLibrary(lib);
    } catch (e) {
      console.error('Error loading user data:', e);
    }
  };

  const fetchCatalog = async () => {
    try {
      const data = await api.getGames({
        genre: selectedGenre,
        max_price: maxPrice || undefined,
        max_duration: maxDuration || undefined,
        search: searchQuery || undefined,
        sort_by: sortBy,
        user_id: 1,
      });
      setGames(data);
    } catch (e) {
      console.error('Error loading games:', e);
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      try {
        const [gList, _] = await Promise.all([
          api.getGenres(),
          refreshUserData(),
        ]);
        setGenres(gList);
        await fetchCatalog();
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  useEffect(() => {
    fetchCatalog();
  }, [selectedGenre, searchQuery, maxPrice, maxDuration, sortBy]);

  // Cart Actions
  const handleAddToCart = async (gameId: number) => {
    try {
      const updatedCart = await api.addToCart(1, gameId);
      setCart(updatedCart);
      await fetchCatalog();
      addToast('success', 'Added game to your cart!');
    } catch (err: any) {
      addToast('error', err.message || 'Could not add to cart.');
    }
  };

  const handleRemoveFromCart = async (gameId: number) => {
    try {
      const updatedCart = await api.removeFromCart(1, gameId);
      setCart(updatedCart);
      await fetchCatalog();
      addToast('info', 'Game removed from cart.');
    } catch (err: any) {
      addToast('error', err.message || 'Could not remove from cart.');
    }
  };

  const handleClearCart = async () => {
    try {
      const updatedCart = await api.clearCart(1);
      setCart(updatedCart);
      await fetchCatalog();
      addToast('info', 'Shopping cart cleared.');
    } catch (err: any) {
      addToast('error', 'Failed to clear cart.');
    }
  };

  // Top Up Action
  const handleTopup = async (amount: number) => {
    try {
      const updatedUser = await api.topupWallet(1, amount);
      setUser(updatedUser);
      if (cart) {
        setCart({
          ...cart,
          user_wallet_balance: updatedUser.wallet_balance,
          is_affordable: updatedUser.wallet_balance >= cart.total_price,
        });
      }
      addToast('success', `Added ₹${amount.toFixed(2)} to your wallet!`);
    } catch (err: any) {
      addToast('error', err.message || 'Top up failed.');
    }
  };

  // AI Assistant Chat Action
  const handleSendMessage = async (text: string, contextualGameId?: number) => {
    const userMsgId = 'user_' + Date.now();
    const userMsg: ChatMessage = {
      id: userMsgId,
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsThinking(true);
    setIsAssistantOpen(true);

    try {
      const targetGameId = contextualGameId !== undefined ? contextualGameId : (selectedGame ? selectedGame.id : null);
      const res = await api.chatWithAssistant(1, text, targetGameId, currentThreadId);
      setCurrentThreadId(res.thread_id);

      const assistantMsg: ChatMessage = {
        id: 'asst_' + Date.now(),
        sender: 'assistant',
        text: res.response,
        thread_id: res.thread_id,
        requires_approval: res.requires_approval,
        approval_data: res.approval_data,
        agent_steps: res.agent_steps,
        recommended_games: res.recommended_games,
        transaction_result: res.transaction_result,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // If approval is requested, open confirmation modal as well
      if (res.requires_approval && res.approval_data) {
        setApprovalSummary(res.approval_data);
        setApprovalThreadId(res.thread_id);
        setApprovalModalOpen(true);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: 'err_' + Date.now(),
          sender: 'assistant',
          text: `⚠️ I encountered an error communicating with the agent workflow: ${err.message}`,
          timestamp: new Date().toLocaleTimeString(),
        }
      ]);
      addToast('error', 'Assistant request failed.');
    } finally {
      setIsThinking(false);
    }
  };

  // Human-in-the-Loop Purchase Approval Execution
  const handleApprovePurchase = async (threadId?: string) => {
    const tId = threadId || approvalThreadId;
    if (!tId) return;
    setApprovalLoading(true);

    try {
      const res = await api.approvePurchase(tId);
      setApprovalModalOpen(false);

      // Add success response to chat stream
      setMessages((prev) => [
        ...prev,
        {
          id: 'appr_' + Date.now(),
          sender: 'assistant',
          text: res.response,
          thread_id: tId,
          agent_steps: res.agent_steps,
          transaction_result: res.transaction_result,
          timestamp: new Date().toLocaleTimeString(),
        }
      ]);

      // Refresh database records
      await refreshUserData();
      await fetchCatalog();

      addToast('success', 'Purchase completed! Games added to My Library.');
    } catch (err: any) {
      addToast('error', err.message || 'Purchase transaction failed.');
    } finally {
      setApprovalLoading(false);
    }
  };

  const handleRejectPurchase = async (threadId?: string) => {
    const tId = threadId || approvalThreadId;
    if (!tId) return;

    try {
      const res = await api.rejectPurchase(tId);
      setApprovalModalOpen(false);

      setMessages((prev) => [
        ...prev,
        {
          id: 'rej_' + Date.now(),
          sender: 'assistant',
          text: res.response,
          thread_id: tId,
          agent_steps: res.agent_steps,
          timestamp: new Date().toLocaleTimeString(),
        }
      ]);
      addToast('info', 'Purchase cancelled.');
    } catch (err: any) {
      addToast('error', 'Cancellation failed.');
    }
  };

  // Cart page proceed button
  const handleProceedCartPurchase = () => {
    handleSendMessage("Buy everything in my cart");
  };

  const handleAskAIAboutCart = () => {
    handleSendMessage("What is currently in my cart, and is it a good combination?");
  };

  // Reset Store Data Action
  const handleResetData = async () => {
    try {
      await api.resetUserData(1);
      await refreshUserData();
      await fetchCatalog();
      addToast('info', 'Store state reset! Library is empty and wallet is ₹3,500.00.');
    } catch (err: any) {
      addToast('error', err.message || 'Failed to reset store state.');
    }
  };

  return (
    <div className="app-container">
      {/* Navigation Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setSelectedGame(null);
          setActiveTab(tab);
        }}
        cartCount={cart?.item_count || 0}
        libraryCount={library.length}
        user={user}
        onOpenAssistant={() => setIsAssistantOpen(true)}
        onOpenTopup={() => setIsTopupOpen(true)}
        onResetData={handleResetData}
      />


      {/* Main Content Body */}
      <main className="main-content">
        {selectedGame ? (
          <GameDetailsPage
            game={selectedGame}
            onBack={() => setSelectedGame(null)}
            onAddToCart={handleAddToCart}
            onRemoveFromCart={handleRemoveFromCart}
            onAskAI={(prompt, gId) => handleSendMessage(prompt, gId)}
          />
        ) : activeTab === 'discover' ? (
          <DiscoverPage
            games={games}
            genres={genres}
            selectedGenre={selectedGenre}
            onSelectGenre={setSelectedGenre}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            maxPrice={maxPrice}
            onMaxPriceChange={setMaxPrice}
            maxDuration={maxDuration}
            onMaxDurationChange={setMaxDuration}
            sortBy={sortBy}
            onSortByChange={setSortBy}
            onSelectGame={(g) => setSelectedGame(g)}
            onAddToCart={handleAddToCart}
            onRemoveFromCart={handleRemoveFromCart}
          />
        ) : activeTab === 'categories' ? (
          <CategoriesPage
            games={games}
            genres={genres}
            onSelectGame={(g) => setSelectedGame(g)}
            onAddToCart={handleAddToCart}
            onRemoveFromCart={handleRemoveFromCart}
          />
        ) : activeTab === 'cart' ? (
          <CartPage
            cart={cart}
            onRemoveItem={handleRemoveFromCart}
            onClearCart={handleClearCart}
            onSelectGame={(g) => setSelectedGame(g)}
            onAskAIAboutCart={handleAskAIAboutCart}
            onProceedToPurchase={handleProceedCartPurchase}
            onOpenTopup={() => setIsTopupOpen(true)}
          />
        ) : (
          <LibraryPage
            library={library}
            onSelectGame={(g) => setSelectedGame(g)}
            onBrowseStore={() => setActiveTab('discover')}
          />
        )}
      </main>

      {/* Embedded Global/Contextual AI Assistant Drawer */}
      <AssistantDrawer
        isOpen={isAssistantOpen}
        onClose={() => setIsAssistantOpen(false)}
        currentGame={selectedGame}
        onSelectGame={(g) => setSelectedGame(g)}
        onAddToCart={handleAddToCart}
        onApprovePurchase={handleApprovePurchase}
        onRejectPurchase={handleRejectPurchase}
        messages={messages}
        onSendMessage={(txt) => handleSendMessage(txt)}
        isThinking={isThinking}
      />

      {/* Top Up Modal */}
      <TopupModal
        isOpen={isTopupOpen}
        onClose={() => setIsTopupOpen(false)}
        currentBalance={user?.wallet_balance || 0}
        onTopup={handleTopup}
      />

      {/* Human-in-the-Loop Purchase Approval Modal */}
      <PurchaseApprovalModal
        isOpen={approvalModalOpen}
        summary={approvalSummary}
        loading={approvalLoading}
        onApprove={() => handleApprovePurchase()}
        onReject={() => handleRejectPurchase()}
      />

      {/* Toast Notifications */}
      <Toast toasts={toasts} onDismiss={removeToast} />
    </div>
  );
};

export default App;
