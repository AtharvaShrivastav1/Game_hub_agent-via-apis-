import React from 'react';
import { Game } from '../types';
import { StarIcon, ClockIcon, ShoppingCartIcon, CheckIcon } from './Icons';

interface GameCardProps {
  game: Game;
  onSelectGame: (game: Game) => void;
  onAddToCart: (gameId: number) => void;
  onRemoveFromCart?: (gameId: number) => void;
}

export const GameCard: React.FC<GameCardProps> = ({
  game,
  onSelectGame,
  onAddToCart,
  onRemoveFromCart,
}) => {
  return (
    <div
      className="glass-card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        cursor: 'pointer',
      }}
      onClick={() => onSelectGame(game)}
    >
      {/* Cover Artwork */}
      <div style={{ position: 'relative', width: '100%', paddingTop: '56.25%', overflow: 'hidden' }}>
        <img
          src={game.image_url}
          alt={game.title}
          loading="lazy"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transition: 'transform 0.4s ease',
          }}
          onMouseOver={(e) => (e.currentTarget.style.transform = 'scale(1.05)')}
          onMouseOut={(e) => (e.currentTarget.style.transform = 'scale(1.0)')}
        />
        
        {/* Genre & Rating overlay */}
        <div style={{
          position: 'absolute',
          top: '10px',
          left: '10px',
          display: 'flex',
          gap: '6px',
        }}>
          <span className="badge badge-genre">{game.genre}</span>
        </div>

        <div style={{
          position: 'absolute',
          bottom: '8px',
          right: '8px',
          background: 'rgba(11, 14, 20, 0.85)',
          backdropFilter: 'blur(6px)',
          padding: '3px 8px',
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          fontSize: '12px',
          fontWeight: 700,
          color: 'var(--accent-gold)',
        }}>
          <StarIcon size={13} />
          <span>{game.rating.toFixed(1)}</span>
        </div>
      </div>

      {/* Card Content */}
      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', flex: 1 }}>
        <div style={{ marginBottom: '8px' }}>
          <h3 style={{
            fontSize: '16px',
            fontWeight: 700,
            color: '#fff',
            marginBottom: '4px',
            lineHeight: 1.3,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}>
            {game.title}
          </h3>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            by {game.developer}
          </div>
        </div>

        <p style={{
          fontSize: '13px',
          color: 'var(--text-secondary)',
          lineHeight: 1.4,
          marginBottom: '14px',
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
          flex: 1,
        }}>
          {game.description}
        </p>

        {/* Metadata: Playtime */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          fontSize: '12px',
          color: 'var(--text-muted)',
          marginBottom: '14px',
        }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <ClockIcon size={13} />
            ~{game.duration_hours}h playtime
          </span>
        </div>

        {/* Price & Action Bar */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingTop: '12px',
          borderTop: '1px solid var(--border-color)',
        }}>
          <div className="badge-price">
            ₹{game.price.toFixed(2)}
          </div>

          <div onClick={(e) => e.stopPropagation()}>
            {game.is_owned ? (
              <span className="badge badge-owned" style={{ padding: '6px 10px' }}>
                <CheckIcon size={14} style={{ marginRight: '4px' }} />
                In Library
              </span>
            ) : game.is_in_cart ? (
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => onRemoveFromCart && onRemoveFromCart(game.id)}
                title="Click to remove from cart"
                style={{ borderColor: 'var(--steam-blue)', color: 'var(--steam-blue)' }}
              >
                <CheckIcon size={14} />
                In Cart
              </button>
            ) : (
              <button
                className="btn btn-steam btn-sm"
                onClick={() => onAddToCart(game.id)}
              >
                <ShoppingCartIcon size={14} />
                Add to Cart
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
