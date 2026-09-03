import React from 'react';
import { Game } from '../types';
import { GameCard } from '../components/GameCard';
import { GameFilters } from '../components/GameFilters';
import { SparklesIcon, ShoppingCartIcon, CheckIcon } from '../components/Icons';

interface DiscoverPageProps {
  games: Game[];
  genres: string[];
  selectedGenre: string;
  onSelectGenre: (genre: string) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  maxPrice: number | null;
  onMaxPriceChange: (p: number | null) => void;
  maxDuration: number | null;
  onMaxDurationChange: (d: number | null) => void;
  sortBy: string;
  onSortByChange: (s: string) => void;
  onSelectGame: (game: Game) => void;
  onAddToCart: (gameId: number) => void;
  onRemoveFromCart: (gameId: number) => void;
}

export const DiscoverPage: React.FC<DiscoverPageProps> = ({
  games,
  genres,
  selectedGenre,
  onSelectGenre,
  searchQuery,
  onSearchChange,
  maxPrice,
  onMaxPriceChange,
  maxDuration,
  onMaxDurationChange,
  sortBy,
  onSortByChange,
  onSelectGame,
  onAddToCart,
  onRemoveFromCart,
}) => {
  // Featured hero game (e.g. highest rated or top game)
  const featured = games.length > 0 ? games[0] : null;

  return (
    <div>
      {/* Featured Game Hero Showcase */}
      {featured && (
        <div
          className="glass-panel"
          style={{
            position: 'relative',
            marginBottom: '32px',
            overflow: 'hidden',
            cursor: 'pointer',
            border: '1px solid rgba(102, 192, 244, 0.25)',
          }}
          onClick={() => onSelectGame(featured)}
        >
          {/* Background blurred backdrop */}
          <div style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: `url(${featured.image_url})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            filter: 'blur(30px) brightness(0.25)',
            transform: 'scale(1.1)',
          }} />

          {/* Hero Content */}
          <div style={{
            position: 'relative',
            padding: '36px',
            display: 'flex',
            flexWrap: 'wrap',
            gap: '30px',
            alignItems: 'center',
          }}>
            <div style={{
              flex: '1 1 340px',
              maxWidth: '540px',
              borderRadius: '10px',
              overflow: 'hidden',
              boxShadow: '0 15px 35px rgba(0,0,0,0.8)',
            }}>
              <img
                src={featured.image_url}
                alt={featured.title}
                style={{ width: '100%', height: 'auto', display: 'block' }}
              />
            </div>

            <div style={{ flex: '1 1 360px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', gap: '8px' }}>
                <span className="badge" style={{ background: 'linear-gradient(135deg, #1999e3, #9333ea)', color: '#fff' }}>
                  <SparklesIcon size={12} style={{ marginRight: '4px' }} />
                  Featured Spotlight
                </span>
                <span className="badge badge-genre">{featured.genre}</span>
              </div>

              <h1 style={{ fontSize: '32px', fontWeight: 900, color: '#fff', lineHeight: 1.2 }}>
                {featured.title}
              </h1>

              <p style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                {featured.description}
              </p>

              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '6px' }}>
                <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                  Developer: <strong style={{ color: 'var(--text-primary)' }}>{featured.developer}</strong>
                </span>
                <span style={{ fontSize: '13px', color: 'var(--accent-gold)', fontWeight: 700 }}>
                  ⭐ {featured.rating.toFixed(1)} / 5.0
                </span>
                <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                  ~{featured.duration_hours} hrs
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '14px' }}>
                <div className="badge-price" style={{ fontSize: '20px', padding: '6px 14px' }}>
                  ₹{featured.price.toFixed(2)}
                </div>

                <div onClick={(e) => e.stopPropagation()}>
                  {featured.is_owned ? (
                    <span className="badge badge-owned" style={{ padding: '10px 18px', fontSize: '13px' }}>
                      <CheckIcon size={16} style={{ marginRight: '6px' }} />
                      In Your Library
                    </span>
                  ) : featured.is_in_cart ? (
                    <button
                      className="btn btn-secondary btn-lg"
                      onClick={() => onRemoveFromCart(featured.id)}
                    >
                      <CheckIcon size={18} />
                      In Cart
                    </button>
                  ) : (
                    <button
                      className="btn btn-steam btn-lg"
                      onClick={() => onAddToCart(featured.id)}
                    >
                      <ShoppingCartIcon size={18} />
                      Add to Cart
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Catalog Filters Bar */}
      <GameFilters
        genres={genres}
        selectedGenre={selectedGenre}
        onSelectGenre={onSelectGenre}
        searchQuery={searchQuery}
        onSearchChange={onSearchChange}
        maxPrice={maxPrice}
        onMaxPriceChange={onMaxPriceChange}
        maxDuration={maxDuration}
        onMaxDurationChange={onMaxDurationChange}
        sortBy={sortBy}
        onSortByChange={onSortByChange}
      />

      {/* Catalog Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#fff', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Browse Games ({games.length})
        </h2>
      </div>

      {/* Games Grid */}
      {games.length === 0 ? (
        <div className="glass-panel" style={{ padding: '60px 20px', textAlign: 'center' }}>
          <p style={{ fontSize: '16px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
            No games found matching your current filters.
          </p>
          <button
            className="btn btn-secondary"
            onClick={() => {
              onSelectGenre('All');
              onSearchChange('');
              onMaxPriceChange(null);
              onMaxDurationChange(null);
            }}
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="games-grid">
          {games.map((g) => (
            <GameCard
              key={g.id}
              game={g}
              onSelectGame={onSelectGame}
              onAddToCart={onAddToCart}
              onRemoveFromCart={onRemoveFromCart}
            />
          ))}
        </div>
      )}
    </div>
  );
};
