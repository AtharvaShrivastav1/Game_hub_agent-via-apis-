import React from 'react';
import { GamepadIcon, ShoppingCartIcon, LibraryIcon, BotIcon, WalletIcon, PlusIcon, SparklesIcon, RotateCcwIcon } from './Icons';
import { User } from '../types';

interface NavbarProps {
  activeTab: 'discover' | 'categories' | 'library' | 'cart';
  setActiveTab: (tab: 'discover' | 'categories' | 'library' | 'cart') => void;
  cartCount: number;
  libraryCount: number;
  user: User | null;
  onOpenAssistant: () => void;
  onOpenTopup: () => void;
  onResetData?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  cartCount,
  libraryCount,
  user,
  onOpenAssistant,
  onOpenTopup,
  onResetData,
}) => {
  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 1000,
      backgroundColor: 'var(--bg-nav)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--border-color)',
    }}>
      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
        padding: '0 20px',
        height: '70px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        {/* Left: Brand Logo & Navigation */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
          <div
            onClick={() => setActiveTab('discover')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              cursor: 'pointer',
              userSelect: 'none',
            }}
          >
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #1999e3 0%, #0d5483 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              boxShadow: '0 0 20px rgba(25, 153, 227, 0.4)',
            }}>
              <GamepadIcon size={24} />
            </div>
            <div>
              <div style={{ fontSize: '20px', fontWeight: 800, letterSpacing: '-0.5px', color: '#fff' }}>
                GAME<span style={{ color: 'var(--steam-blue)' }}>HUB</span>
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                Agentic Store
              </div>
            </div>
          </div>

          <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              className={`btn ${activeTab === 'discover' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('discover')}
              style={{ fontSize: '14px', padding: '8px 14px' }}
            >
              Discover
            </button>
            <button
              className={`btn ${activeTab === 'categories' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('categories')}
              style={{ fontSize: '14px', padding: '8px 14px' }}
            >
              Categories
            </button>
            <button
              className={`btn ${activeTab === 'library' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('library')}
              style={{ fontSize: '14px', padding: '8px 14px', position: 'relative' }}
            >
              <LibraryIcon size={16} />
              My Library
              {libraryCount > 0 && (
                <span style={{
                  background: 'rgba(255,255,255,0.15)',
                  color: '#fff',
                  fontSize: '11px',
                  fontWeight: 700,
                  padding: '1px 6px',
                  borderRadius: '10px',
                  marginLeft: '4px',
                }}>
                  {libraryCount}
                </span>
              )}
            </button>
            <button
              className={`btn ${activeTab === 'cart' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('cart')}
              style={{ fontSize: '14px', padding: '8px 14px', position: 'relative' }}
            >
              <ShoppingCartIcon size={16} />
              Cart
              {cartCount > 0 && (
                <span style={{
                  background: 'linear-gradient(135deg, #75b022, #588a1b)',
                  color: '#fff',
                  fontSize: '11px',
                  fontWeight: 800,
                  padding: '2px 7px',
                  borderRadius: '10px',
                  marginLeft: '4px',
                  boxShadow: '0 0 8px rgba(117, 176, 34, 0.6)',
                }}>
                  {cartCount}
                </span>
              )}
            </button>
          </nav>
        </div>

        {/* Right: AI Assistant & Wallet Profile & Reset Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* AI Assistant Button */}
          <button
            onClick={onOpenAssistant}
            className="btn"
            style={{
              background: 'linear-gradient(135deg, rgba(147, 51, 234, 0.25) 0%, rgba(102, 192, 244, 0.25) 100%)',
              border: '1px solid rgba(147, 51, 234, 0.4)',
              color: '#fff',
              padding: '8px 16px',
              borderRadius: '20px',
              boxShadow: '0 0 15px rgba(147, 51, 234, 0.25)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <SparklesIcon size={16} style={{ color: '#c084fc' }} />
            <span style={{ fontWeight: 700 }}>AI Assistant</span>
            <span style={{
              width: '8px',
              height: '8px',
              backgroundColor: '#34d399',
              borderRadius: '50%',
              boxShadow: '0 0 8px #34d399',
              marginLeft: '2px',
            }} />
          </button>

          {/* User Wallet Balance Bar */}
          {user && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-color)',
              borderRadius: '24px',
              padding: '4px 6px 4px 14px',
              gap: '12px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <WalletIcon size={16} style={{ color: 'var(--steam-blue)' }} />
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1 }}>Wallet</div>
                  <div style={{ fontSize: '14px', fontWeight: 800, color: '#a4d007', lineHeight: 1.2 }}>
                    ₹{user.wallet_balance.toFixed(2)}
                  </div>
                </div>
              </div>

              <button
                onClick={onOpenTopup}
                title="Top up wallet balance"
                className="btn btn-secondary btn-sm"
                style={{
                  borderRadius: '14px',
                  padding: '4px 8px',
                  fontSize: '11px',
                  background: 'rgba(255, 255, 255, 0.06)',
                }}
              >
                <PlusIcon size={12} />
                Top Up
              </button>
            </div>
          )}

          {/* Reset / Refresh Data Button */}
          {onResetData && (
            <button
              onClick={onResetData}
              title="Reset state: clear library, cart, and restore ₹3,500 balance"
              className="btn btn-secondary btn-sm"
              style={{
                borderRadius: '14px',
                padding: '7px 10px',
                fontSize: '12px',
                background: 'rgba(239, 68, 68, 0.12)',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                color: '#fca5a5',
              }}
            >
              <RotateCcwIcon size={14} />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};

