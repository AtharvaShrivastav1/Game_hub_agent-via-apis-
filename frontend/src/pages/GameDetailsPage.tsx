import React, { useState } from 'react';
import { Game } from '../types';
import { ArrowLeftIcon, StarIcon, ClockIcon, ShoppingCartIcon, CheckIcon, BotIcon, SparklesIcon, SendIcon } from '../components/Icons';

interface GameDetailsPageProps {
  game: Game;
  onBack: () => void;
  onAddToCart: (gameId: number) => void;
  onRemoveFromCart: (gameId: number) => void;
  onAskAI: (message: string, gameId: number) => void;
}

export const GameDetailsPage: React.FC<GameDetailsPageProps> = ({
  game,
  onBack,
  onAddToCart,
  onRemoveFromCart,
  onAskAI,
}) => {
  const [customQuestion, setCustomQuestion] = useState('');

  const contextualPrompts = [
    "Is this worth buying?",
    "How long will this take to complete?",
    `Compare this with another ${game.genre} under ₹2000`,
    "Recommend games similar to this",
    "What are players praising about this title?",
  ];

  const handleSendCustom = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customQuestion.trim()) return;
    onAskAI(customQuestion.trim(), game.id);
    setCustomQuestion('');
  };

  return (
    <div>
      {/* Back Button */}
      <button
        onClick={onBack}
        className="btn btn-secondary"
        style={{ marginBottom: '20px' }}
      >
        <ArrowLeftIcon size={16} />
        Back to Store
      </button>

      {/* Main Details Panel */}
      <div className="glass-panel" style={{ overflow: 'hidden', marginBottom: '28px' }}>
        {/* Banner with blur backdrop */}
        <div style={{
          position: 'relative',
          height: '380px',
          width: '100%',
          overflow: 'hidden',
          backgroundColor: '#0a0e14',
        }}>
          <img
            src={game.image_url}
            alt={game.title}
            style={{
              position: 'absolute',
              inset: 0,
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              filter: 'brightness(0.55)',
            }}
          />

          <div style={{
            position: 'absolute',
            inset: 0,
            background: 'linear-gradient(to top, #131b26 0%, transparent 60%)',
          }} />

          {/* Title Header overlay */}
          <div style={{
            position: 'absolute',
            bottom: '24px',
            left: '30px',
            right: '30px',
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'space-between',
            alignItems: 'flex-end',
            gap: '16px',
          }}>
            <div>
              <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                <span className="badge badge-genre">{game.genre}</span>
                <span className="badge" style={{ background: 'rgba(245, 158, 11, 0.2)', color: 'var(--accent-gold)' }}>
                  <StarIcon size={12} style={{ marginRight: '4px' }} />
                  {game.rating.toFixed(1)} / 5.0 Rating
                </span>
              </div>
              <h1 style={{ fontSize: '36px', fontWeight: 900, color: '#fff', lineHeight: 1.1 }}>
                {game.title}
              </h1>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Developed by <strong style={{ color: '#fff' }}>{game.developer}</strong> • Released {game.release_date}
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div className="badge-price" style={{ fontSize: '24px', padding: '8px 18px' }}>
                ₹{game.price.toFixed(2)}
              </div>

              {game.is_owned ? (
                <span className="badge badge-owned" style={{ padding: '12px 20px', fontSize: '14px' }}>
                  <CheckIcon size={18} style={{ marginRight: '6px' }} />
                  In Your Library
                </span>
              ) : game.is_in_cart ? (
                <button
                  className="btn btn-secondary btn-lg"
                  onClick={() => onRemoveFromCart(game.id)}
                >
                  <CheckIcon size={18} />
                  In Cart (Click to Remove)
                </button>
              ) : (
                <button
                  className="btn btn-steam btn-lg"
                  onClick={() => onAddToCart(game.id)}
                >
                  <ShoppingCartIcon size={18} />
                  Add to Cart
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Description & Technical Specs */}
        <div style={{ padding: '30px', display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '30px' }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#fff', marginBottom: '12px' }}>
              About This Game
            </h3>
            <p style={{ fontSize: '15px', color: 'var(--text-secondary)', lineHeight: 1.7, whiteSpace: 'pre-line' }}>
              {game.description}
            </p>
          </div>

          {/* Quick Info Sidebar */}
          <div style={{
            background: 'var(--bg-surface)',
            borderRadius: '8px',
            padding: '20px',
            border: '1px solid var(--border-color)',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
            height: 'fit-content',
          }}>
            <h4 style={{ fontSize: '14px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)' }}>
              Game Details
            </h4>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Genre</span>
              <span style={{ color: '#fff', fontWeight: 600 }}>{game.genre}</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Playtime</span>
              <span style={{ color: '#fff', fontWeight: 600 }}>~{game.duration_hours} hours</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Release Date</span>
              <span style={{ color: '#fff', fontWeight: 600 }}>{game.release_date}</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Developer</span>
              <span style={{ color: '#fff', fontWeight: 600 }}>{game.developer}</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>User Rating</span>
              <span style={{ color: 'var(--accent-gold)', fontWeight: 700 }}>⭐ {game.rating.toFixed(1)} / 5.0</span>
            </div>
          </div>
        </div>
      </div>

      {/* Embedded Contextual AI Assistant Section */}
      <div className="glass-panel" style={{ padding: '28px', border: '1px solid rgba(147, 51, 234, 0.3)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <div style={{
            padding: '10px',
            background: 'linear-gradient(135deg, rgba(147, 51, 234, 0.2), rgba(102, 192, 244, 0.2))',
            borderRadius: '10px',
            color: '#c084fc',
          }}>
            <BotIcon size={24} />
          </div>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>
              Ask AI about {game.title}
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              Contextually grounded in GameHub database catalog. The AI automatically understands "this" refers to {game.title}.
            </p>
          </div>
        </div>

        {/* Suggestion Chips */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginBottom: '20px' }}>
          {contextualPrompts.map((prompt, idx) => (
            <button
              key={idx}
              className="btn btn-secondary"
              style={{
                borderRadius: '20px',
                fontSize: '13px',
                padding: '8px 14px',
                background: 'rgba(255, 255, 255, 0.05)',
              }}
              onClick={() => onAskAI(prompt, game.id)}
            >
              <SparklesIcon size={14} style={{ color: 'var(--steam-blue)' }} />
              "{prompt}"
            </button>
          ))}
        </div>

        {/* Custom Input */}
        <form onSubmit={handleSendCustom} style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            placeholder={`Ask any specific question about ${game.title}...`}
            value={customQuestion}
            onChange={(e) => setCustomQuestion(e.target.value)}
            style={{
              flex: 1,
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              padding: '12px 16px',
              color: '#fff',
              fontSize: '14px',
              outline: 'none',
            }}
            onFocus={(e) => (e.currentTarget.style.borderColor = 'var(--steam-blue)')}
            onBlur={(e) => (e.currentTarget.style.borderColor = 'var(--border-color)')}
          />
          <button type="submit" className="btn btn-primary btn-lg" disabled={!customQuestion.trim()}>
            <SendIcon size={16} />
            Ask Assistant
          </button>
        </form>
      </div>
    </div>
  );
};
