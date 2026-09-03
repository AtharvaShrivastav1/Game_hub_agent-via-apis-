import React, { useState } from 'react';
import { WalletIcon, XIcon, PlusIcon } from './Icons';

interface TopupModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentBalance: number;
  onTopup: (amount: number) => Promise<void>;
}

export const TopupModal: React.FC<TopupModalProps> = ({
  isOpen,
  onClose,
  currentBalance,
  onTopup,
}) => {
  const [amount, setAmount] = useState<number>(1000);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleConfirm = async () => {
    if (amount <= 0) return;
    setLoading(true);
    try {
      await onTopup(amount);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const presetAmounts = [500, 1000, 2000, 5000];

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '16px',
    }}>
      <div className="glass-panel" style={{
        maxWidth: '440px',
        width: '100%',
        padding: '24px',
        position: 'relative',
        boxShadow: '0 20px 50px rgba(0,0,0,0.8), 0 0 30px rgba(102, 192, 244, 0.2)',
      }}>
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            background: 'none',
            border: 'none',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
          }}
        >
          <XIcon size={20} />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <div style={{
            padding: '10px',
            background: 'rgba(102, 192, 244, 0.15)',
            borderRadius: '10px',
            color: 'var(--steam-blue)',
          }}>
            <WalletIcon size={24} />
          </div>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Top Up Steam Wallet</h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              Current balance: <strong style={{ color: '#a4d007' }}>₹{currentBalance.toFixed(2)}</strong>
            </p>
          </div>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
            Select Amount:
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginBottom: '12px' }}>
            {presetAmounts.map((amt) => (
              <button
                key={amt}
                type="button"
                className={`btn ${amount === amt ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '13px', padding: '8px 0' }}
                onClick={() => setAmount(amt)}
              >
                ₹{amt}
              </button>
            ))}
          </div>

          <div style={{ position: 'relative' }}>
            <span style={{ position: 'absolute', left: '12px', top: '10px', color: 'var(--text-secondary)' }}>₹</span>
            <input
              type="number"
              min="50"
              step="50"
              value={amount}
              onChange={(e) => setAmount(Number(e.target.value))}
              style={{
                width: '100%',
                background: '#0d131b',
                border: '1px solid var(--border-color)',
                borderRadius: '6px',
                padding: '10px 12px 10px 28px',
                color: '#fff',
                fontSize: '15px',
                fontWeight: 600,
                outline: 'none',
              }}
            />
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
          <button className="btn btn-secondary" onClick={onClose} disabled={loading}>
            Cancel
          </button>
          <button className="btn btn-steam" onClick={handleConfirm} disabled={loading}>
            <PlusIcon size={16} />
            {loading ? 'Processing...' : `Add ₹${amount} to Wallet`}
          </button>
        </div>
      </div>
    </div>
  );
};
