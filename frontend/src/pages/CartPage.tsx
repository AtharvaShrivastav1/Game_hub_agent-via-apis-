import React from 'react';
import { CartSummary, Game } from '../types';
import { TrashIcon, ShoppingCartIcon, CheckIcon, BotIcon, WalletIcon, PlusIcon } from '../components/Icons';

interface CartPageProps {
  cart: CartSummary | null;
  onRemoveItem: (gameId: number) => void;
  onClearCart: () => void;
  onSelectGame: (game: Game) => void;
  onAskAIAboutCart: () => void;
  onProceedToPurchase: () => void;
  onOpenTopup: () => void;
}

export const CartPage: React.FC<CartPageProps> = ({
  cart,
  onRemoveItem,
  onClearCart,
  onSelectGame,
  onAskAIAboutCart,
  onProceedToPurchase,
  onOpenTopup,
}) => {
  const items = cart?.items || [];
  const totalPrice = cart?.total_price || 0;
  const wallet = cart?.user_wallet_balance || 0;
  const isAffordable = cart?.is_affordable || false;
  const shortfall = Math.max(0, totalPrice - wallet);

  if (items.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '80px 20px', textAlign: 'center' }}>
        <div style={{
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          background: 'rgba(102, 192, 244, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--steam-blue)',
          margin: '0 auto 16px',
        }}>
          <ShoppingCartIcon size={32} />
        </div>
        <h2 style={{ fontSize: '24px', fontWeight: 800, color: '#fff', marginBottom: '8px' }}>
          Your Cart is Empty
        </h2>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)', maxWidth: '400px', margin: '0 auto 24px' }}>
          Explore our extensive catalog of indie gems, action thrillers, and immersive RPGs to add games to your cart!
        </p>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 800, color: '#fff' }}>
          Your Shopping Cart ({items.length})
        </h1>
        <button className="btn btn-secondary btn-sm" onClick={onClearCart}>
          <TrashIcon size={14} />
          Clear All
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '30px', alignItems: 'flex-start' }}>
        {/* Cart Items List */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {items.map((item) => (
            <div
              key={item.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                background: 'var(--bg-surface)',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                gap: '16px',
              }}
            >
              {/* Thumbnail */}
              <img
                src={item.game.image_url}
                alt={item.game.title}
                style={{
                  width: '90px',
                  height: '52px',
                  objectFit: 'cover',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
                onClick={() => onSelectGame(item.game)}
              />

              {/* Title & Info */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <h4
                  style={{
                    fontSize: '15px',
                    fontWeight: 700,
                    color: '#fff',
                    cursor: 'pointer',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                  onClick={() => onSelectGame(item.game)}
                >
                  {item.game.title}
                </h4>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {item.game.genre} • ~{item.game.duration_hours}h playtime
                </div>
              </div>

              {/* Price & Remove */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <span className="badge-price" style={{ fontSize: '15px' }}>
                  ₹{item.game.price.toFixed(2)}
                </span>
                <button
                  onClick={() => onRemoveItem(item.game.id)}
                  title="Remove from cart"
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    padding: '6px',
                    borderRadius: '4px',
                  }}
                  onMouseOver={(e) => (e.currentTarget.style.color = 'var(--accent-red)')}
                  onMouseOut={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
                >
                  <TrashIcon size={18} />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Order Summary Card */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#fff' }}>
            Order Summary
          </h3>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px', color: 'var(--text-secondary)' }}>
            <span>Subtotal ({items.length} items):</span>
            <strong style={{ color: '#fff', fontSize: '16px' }}>₹{totalPrice.toFixed(2)}</strong>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px', color: 'var(--text-secondary)' }}>
            <span>Current Wallet Balance:</span>
            <span style={{ color: '#a4d007', fontWeight: 600 }}>₹{wallet.toFixed(2)}</span>
          </div>

          <div style={{
            height: '1px',
            backgroundColor: 'var(--border-color)',
            margin: '4px 0',
          }} />

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '16px', fontWeight: 800 }}>
            <span>Estimated Total:</span>
            <span style={{ color: '#a4d007', fontSize: '20px' }}>₹{totalPrice.toFixed(2)}</span>
          </div>

          {/* Affordability Warning / Top Up prompt */}
          {!isAffordable && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '8px',
              padding: '12px',
              fontSize: '13px',
              color: '#fca5a5',
            }}>
              <div>⚠️ Shortfall of <strong>₹{shortfall.toFixed(2)}</strong></div>
              <button
                className="btn btn-secondary btn-sm"
                onClick={onOpenTopup}
                style={{ marginTop: '8px', width: '100%' }}
              >
                <PlusIcon size={14} />
                Add ₹{Math.ceil(shortfall / 100) * 100} to Wallet
              </button>
            </div>
          )}

          {/* AI Assistance button */}
          <button
            className="btn btn-secondary"
            onClick={onAskAIAboutCart}
            style={{ width: '100%', borderColor: 'rgba(147, 51, 234, 0.4)' }}
          >
            <BotIcon size={16} style={{ color: '#c084fc' }} />
            Ask AI about Cart Combination
          </button>

          {/* Proceed to Purchase button (Triggers HITL gate) */}
          <button
            className="btn btn-steam btn-lg"
            onClick={onProceedToPurchase}
            disabled={!isAffordable}
            style={{
              width: '100%',
              opacity: !isAffordable ? 0.6 : 1,
              cursor: !isAffordable ? 'not-allowed' : 'pointer',
            }}
          >
            <CheckIcon size={18} />
            Purchase with AI Approval
          </button>

          <p style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center' }}>
            🔒 Purchases are atomic and protected by the LangGraph Human-in-the-Loop verification gate.
          </p>
        </div>
      </div>
    </div>
  );
};
