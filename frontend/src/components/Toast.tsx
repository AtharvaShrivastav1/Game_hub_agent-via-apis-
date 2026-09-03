import React, { useEffect } from 'react';
import { CheckIcon, XIcon, ShieldAlertIcon } from './Icons';

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info';
  text: string;
}

interface ToastProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

export const Toast: React.FC<ToastProps> = ({ toasts, onDismiss }) => {
  return (
    <div style={{
      position: 'fixed',
      bottom: '24px',
      left: '24px',
      zIndex: 11000,
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
      maxWidth: '380px',
    }}>
      {toasts.map((toast) => (
        <div
          key={toast.id}
          style={{
            backgroundColor: toast.type === 'success' ? '#183818' : toast.type === 'error' ? '#451a1a' : '#172738',
            border: '1px solid',
            borderColor: toast.type === 'success' ? '#5c7e10' : toast.type === 'error' ? '#ef4444' : '#66c0f4',
            color: '#fff',
            borderRadius: '8px',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
            fontSize: '13px',
            animation: 'fadeIn 0.2s ease',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {toast.type === 'success' && <CheckIcon size={16} style={{ color: '#a4d007' }} />}
            {toast.type === 'error' && <ShieldAlertIcon size={16} style={{ color: '#ef4444' }} />}
            {toast.type === 'info' && <span style={{ color: '#66c0f4' }}>ℹ️</span>}
            <span>{toast.text}</span>
          </div>

          <button
            onClick={() => onDismiss(toast.id)}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '2px',
            }}
          >
            <XIcon size={14} />
          </button>
        </div>
      ))}
    </div>
  );
};
