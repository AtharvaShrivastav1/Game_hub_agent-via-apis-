import React from 'react';
import { Game } from '../types';
import { GameCard } from '../components/GameCard';

interface CategoriesPageProps {
  games: Game[];
  genres: string[];
  onSelectGame: (game: Game) => void;
  onAddToCart: (gameId: number) => void;
  onRemoveFromCart: (gameId: number) => void;
}

export const CategoriesPage: React.FC<CategoriesPageProps> = ({
  games,
  genres,
  onSelectGame,
  onAddToCart,
  onRemoveFromCart,
}) => {
  return (
    <div>
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 800, color: '#fff' }}>
          Game Categories & Genres
        </h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Explore curated collections of titles categorized across genres.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '40px' }}>
        {genres.map((genre) => {
          const genreGames = games.filter((g) => g.genre.toLowerCase() === genre.toLowerCase());
          if (genreGames.length === 0) return null;

          return (
            <div key={genre}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '16px',
                borderBottom: '1px solid var(--border-color)',
                paddingBottom: '8px',
              }}>
                <h2 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--steam-blue)' }}>
                  {genre} ({genreGames.length})
                </h2>
              </div>

              <div className="games-grid">
                {genreGames.map((g) => (
                  <GameCard
                    key={g.id}
                    game={g}
                    onSelectGame={onSelectGame}
                    onAddToCart={onAddToCart}
                    onRemoveFromCart={onRemoveFromCart}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
