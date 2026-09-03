import React, { useState, useRef, useEffect } from 'react';
import { Game, ChatMessage, PurchaseSummary } from '../types';
import { BotIcon, SparklesIcon, XIcon, SendIcon, CheckIcon, ShieldAlertIcon, ClockIcon, StarIcon } from './Icons';

interface AssistantDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  currentGame: Game | null;
  onSelectGame: (game: Game) => void;
  onAddToCart: (gameId: number) => void;
  onApprovePurchase: (threadId: string) => Promise<void>;
  onRejectPurchase: (threadId: string) => Promise<void>;
  messages: ChatMessage[];
  onSendMessage: (text: string) => Promise<void>;
  isThinking: boolean;
}

export const AssistantDrawer: React.FC<AssistantDrawerProps> = ({
  isOpen,
  onClose,
  currentGame,
  onSelectGame,
  onAddToCart,
  onApprovePurchase,
  onRejectPurchase,
  messages,
  onSendMessage,
  isThinking,
}) => {
  const [input, setInput] = useState('');
  const [showSteps, setShowSteps] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  if (!isOpen) return null;

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const text = input.trim();
    if (!text || isThinking) return;
    setInput('');
    await onSendMessage(text);
  };

  const handleChipClick = (prompt: string) => {
    onSendMessage(prompt);
  };

  const toggleSteps = (id: string) => {
    setShowSteps((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const contextualChips = currentGame ? [
    `Is this worth buying?`,
    `Compare this with another RPG under ₹2000`,
    `How long will this take to complete?`,
    `Recommend something similar`,
    `Buy this game`,
  ] : [
    'Recommend an RPG under ₹1500',
    'I have ₹3000. What games should I buy?',
    'Find games I can finish in under 20 hours',
    "What's in my cart?",
    'Buy everything in my cart',
  ];

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      right: 0,
      bottom: 0,
      width: '460px',
      maxWidth: '100vw',
      backgroundColor: 'rgba(15, 21, 30, 0.95)',
      backdropFilter: 'blur(20px)',
      borderLeft: '1px solid rgba(102, 192, 244, 0.25)',
      boxShadow: '-10px 0 40px rgba(0, 0, 0, 0.8)',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 9990,
      animation: 'slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
    }}>
      {/* Header */}
      <div style={{
        padding: '18px 20px',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'rgba(23, 31, 44, 0.6)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #9333ea 0%, #66c0f4 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            boxShadow: '0 0 15px rgba(147, 51, 234, 0.4)',
          }}>
            <BotIcon size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>GameHub AI</h3>
              <span className="badge badge-genre" style={{ fontSize: '10px', padding: '1px 5px' }}>LangGraph</span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
              Orchestrator • Research • Recommendation • Purchase
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            padding: '6px',
            borderRadius: '6px',
          }}
        >
          <XIcon size={20} />
        </button>
      </div>

      {/* Active Game Context Banner if viewing details */}
      {currentGame && (
        <div style={{
          padding: '8px 16px',
          background: 'rgba(102, 192, 244, 0.1)',
          borderBottom: '1px solid rgba(102, 192, 244, 0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '12px',
        }}>
          <span style={{ color: 'var(--steam-blue)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <SparklesIcon size={14} />
            Context: <strong>{currentGame.title}</strong>
          </span>
          <span style={{ color: 'var(--text-muted)' }}>₹{currentGame.price}</span>
        </div>
      )}

      {/* Suggestion Chips */}
      <div style={{
        padding: '10px 16px',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        gap: '6px',
        overflowX: 'auto',
        scrollbarWidth: 'none',
        background: 'rgba(11, 14, 20, 0.4)',
      }}>
        {contextualChips.map((chip, idx) => (
          <button
            key={idx}
            onClick={() => handleChipClick(chip)}
            disabled={isThinking}
            style={{
              whiteSpace: 'nowrap',
              fontSize: '11px',
              padding: '4px 10px',
              borderRadius: '12px',
              backgroundColor: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onMouseOver={(e) => (e.currentTarget.style.backgroundColor = 'rgba(102, 192, 244, 0.15)')}
            onMouseOut={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.06)')}
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Messages Feed */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}>
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <div style={{
              maxWidth: '90%',
              padding: '12px 16px',
              borderRadius: msg.sender === 'user' ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
              backgroundColor: msg.sender === 'user' ? '#1b4369' : '#172230',
              border: '1px solid',
              borderColor: msg.sender === 'user' ? 'rgba(102, 192, 244, 0.4)' : 'rgba(255, 255, 255, 0.08)',
              color: '#fff',
              fontSize: '14px',
              lineHeight: 1.5,
              whiteSpace: 'pre-wrap',
            }}>
              {msg.text}
            </div>

            {/* Agent Telemetry Step Logs */}
            {msg.agent_steps && msg.agent_steps.length > 0 && (
              <div style={{ marginTop: '6px', maxWidth: '90%', width: '100%' }}>
                <button
                  onClick={() => toggleSteps(msg.id)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-muted)',
                    fontSize: '11px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '2px 0',
                  }}
                >
                  <SparklesIcon size={12} style={{ color: 'var(--steam-blue)' }} />
                  {showSteps[msg.id] ? 'Hide LangGraph Agent Steps ▲' : `View ${msg.agent_steps.length} Agent Steps ▼`}
                </button>

                {showSteps[msg.id] && (
                  <div style={{
                    marginTop: '4px',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    background: 'rgba(0, 0, 0, 0.4)',
                    border: '1px solid var(--border-color)',
                    fontSize: '12px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px',
                  }}>
                    {msg.agent_steps.map((step, idx) => (
                      <div key={idx} style={{ borderLeft: '2px solid var(--steam-blue)', paddingLeft: '8px' }}>
                        <div style={{ fontWeight: 700, color: 'var(--steam-blue)', fontSize: '11px' }}>
                          {step.agent_name}
                        </div>
                        <div style={{ color: 'var(--text-primary)', fontSize: '11px' }}>
                          {step.action}
                        </div>
                        {step.details && (
                          <div style={{ color: 'var(--text-muted)', fontSize: '10px' }}>
                            {step.details}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* In-Chat Purchase Approval Card */}
            {msg.requires_approval && msg.approval_data && (
              <div style={{
                marginTop: '10px',
                maxWidth: '92%',
                width: '100%',
                background: 'rgba(23, 33, 47, 0.95)',
                border: '1px solid rgba(245, 158, 11, 0.4)',
                borderRadius: '10px',
                padding: '14px',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6), 0 0 20px rgba(245, 158, 11, 0.2)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--accent-gold)' }}>
                  <ShieldAlertIcon size={18} />
                  <span style={{ fontSize: '12px', fontWeight: 800, textTransform: 'uppercase' }}>
                    Human Approval Required
                  </span>
                </div>

                <div style={{ fontSize: '13px', color: '#fff', marginBottom: '10px' }}>
                  Purchase: <strong>{msg.approval_data.game_titles.join(', ')}</strong>
                </div>

                <div style={{
                  background: 'rgba(0, 0, 0, 0.3)',
                  padding: '8px 10px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                  marginBottom: '12px',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
                    <span>Total Cost:</span>
                    <strong style={{ color: '#fff' }}>₹{msg.approval_data.total_price.toFixed(2)}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
                    <span>Wallet Balance:</span>
                    <span>₹{msg.approval_data.current_wallet_balance.toFixed(2)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, color: '#a4d007' }}>
                    <span>Remaining Balance:</span>
                    <span>₹{msg.approval_data.remaining_balance.toFixed(2)}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => msg.thread_id && onRejectPurchase(msg.thread_id)}
                    style={{ flex: 1 }}
                  >
                    <XIcon size={14} />
                    Reject
                  </button>
                  <button
                    className="btn btn-steam btn-sm"
                    onClick={() => msg.thread_id && onApprovePurchase(msg.thread_id)}
                    style={{ flex: 1.2 }}
                  >
                    <CheckIcon size={14} />
                    Approve Purchase
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}

        {isThinking && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--steam-blue)', fontSize: '13px' }}>
            <div style={{
              width: '18px',
              height: '18px',
              border: '2px solid rgba(102, 192, 244, 0.2)',
              borderTopColor: 'var(--steam-blue)',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
            }} />
            <span>Orchestrating agents & querying database...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <form
        onSubmit={handleSend}
        style={{
          padding: '14px 16px',
          borderTop: '1px solid var(--border-color)',
          background: 'rgba(19, 27, 38, 0.9)',
          display: 'flex',
          gap: '8px',
          alignItems: 'center',
        }}
      >
        <input
          type="text"
          placeholder={currentGame ? `Ask AI about ${currentGame.title}...` : "Ask AI about games, budget, recommendations, or say 'Buy Witcher'..."}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isThinking}
          style={{
            flex: 1,
            backgroundColor: '#0d131b',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            padding: '10px 14px',
            color: '#fff',
            fontSize: '13px',
            outline: 'none',
          }}
          onFocus={(e) => (e.currentTarget.style.borderColor = 'var(--steam-blue)')}
          onBlur={(e) => (e.currentTarget.style.borderColor = 'var(--border-color)')}
        />
        <button
          type="submit"
          className="btn btn-primary"
          disabled={!input.trim() || isThinking}
          style={{ padding: '10px 16px' }}
        >
          <SendIcon size={16} />
        </button>
      </form>
    </div>
  );
};
