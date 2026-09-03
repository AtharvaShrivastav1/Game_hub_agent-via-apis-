import React from 'react';
import { PurchaseSummary } from '../types';
import { ShieldAlertIcon, CheckIcon, XIcon, WalletIcon } from './Icons';

interface PurchaseApprovalModalProps {
  isOpen: boolean;
  summary: PurchaseSummary | null;
  loading: boolean;
  onApprove: () => void;
  onReject: () => void;
}

export const PurchaseApprovalModal: React.FC<PurchaseApprovalModalProps> = ({
  isOpen,
  summary,
  loading,
  onApprove,
  onReject,
}) => {
  if (!isOpen || !summary) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.85)',
      backdropFilter: 'blur(10px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 10000,
      padding: '16px',
    }}>
      <div className="glass-panel" style={{
        maxWidth: '520px',
        width: '100%',
        padding: '28px',
        position: 'relative',
        boxShadow: '0 25px 60px rgba(0,0,0,0.9), 0 0 40px rgba(102, 192, 244, 0.25)',
        border: '1px solid rgba(102, 192, 244, 0.3)',
      }}>
        {/* Header Alert */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px', marginBottom: '20px' }}>
          <div style={{
            padding: '12px',
            background: 'rgba(245, 158, 11, 0.15)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            borderRadius: '12px',
            color: 'var(--accent-gold)',
          }}>
            <ShieldAlertIcon size={28} />
          </div>
          <div>
            <div style={{
              fontSize: '11px',
              textTransform: 'uppercase',
              color: 'var(--accent-gold)',
              fontWeight: 800,
              letterSpacing: '1px',
            }}>
              Human-in-the-Loop Gate
            </div>
            <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#fff', marginTop: '2px' }}>
              Purchase Confirmation Required
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              LangGraph agent paused execution awaiting your explicit authorization.
            </p>
          </div>
        </div>

        {/* Purchase Items List */}
        <div style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '20px',
        }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase' }}>
            Selected Game(s)
          </div>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {summary.game_titles.map((title, idx) => (
              <li key={idx} style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '15px',
                fontWeight: 600,
                color: '#fff',
              }}>
                <span>🎮 {title}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Financial Breakdown Table */}
        <div style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px', color: 'var(--text-secondary)' }}>
            <span>Total Purchase Price:</span>
            <strong style={{ color: '#fff' }}>₹{summary.total_price.toFixed(2)}</strong>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px', color: 'var(--text-secondary)' }}>
            <span>Current Wallet Balance:</span>
            <span style={{ color: '#fff' }}>₹{summary.current_wallet_balance.toFixed(2)}</span>
          </div>

          <div style={{
            height: '1px',
            backgroundColor: 'var(--border-color)',
            margin: '4px 0',
          }} />

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '15px', fontWeight: 700 }}>
            <span>Remaining Balance After:</span>
            <span style={{ color: summary.can_afford ? '#a4d007' : 'var(--accent-red)' }}>
              ₹{summary.remaining_balance.toFixed(2)}
            </span>
          </div>

          {!summary.can_afford && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '6px',
              padding: '10px',
              fontSize: '12px',
              color: '#fca5a5',
              marginTop: '4px',
            }}>
              ⚠️ Insufficient balance! Please top up your wallet before approving.
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <button
            className="btn btn-secondary btn-lg"
            onClick={onReject}
            disabled={loading}
            style={{ flex: 1 }}
          >
            <XIcon size={18} />
            Reject / Cancel
          </button>

          <button
            className="btn btn-steam btn-lg"
            onClick={onApprove}
            disabled={loading || !summary.can_afford}
            style={{
              flex: 1.3,
              opacity: !summary.can_afford ? 0.5 : 1,
              cursor: !summary.can_afford ? 'not-allowed' : 'pointer',
            }}
          >
            <CheckIcon size={18} />
            {loading ? 'Executing Transaction...' : 'Approve Purchase'}
          </button>
        </div>
      </div>
    </div>
  );
};
