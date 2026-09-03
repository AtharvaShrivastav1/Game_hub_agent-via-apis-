import React, { useState } from 'react';
import { Game } from '../types';
import { LibraryIcon, CheckIcon, StarIcon, ClockIcon, SearchIcon, GamepadIcon } from '../components/Icons';

interface LibraryPageProps {
  library: Game[];
  onSelectGame: (game: Game) => void;
  onBrowseStore: () => void;
}

export const LibraryPage: React.FC<LibraryPageProps> = ({
  library,
  onSelectGame,
  onBrowseStore,
}) => {
  const [search, setSearch] = useState('');
  const [playingId, setPlayingId] = useState<number | null>(null);

  const filtered = library.filter((g) =>
    g.title.toLowerCase().includes(search.toLowerCase()) ||
    g.genre.toLowerCase().includes(search.toLowerCase())
  );

  const handleLaunch = (gameId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setPlayingId(gameId);
    setTimeout(() => {
      setPlayingId(null);
    }, 4000);
  };

  if (library.length === 0) {
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
          <LibraryIcon size={32} />
        </div>
        <h2 style={{ fontSize: '24px', fontWeight: 800, color: '#fff', marginBottom: '8px' }}>
          Your Library is Empty
        </h2>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)', maxWidth: '400px', margin: '0 auto 24px' }}>
          Games you purchase via GameHub and the AI assistant will be permanently stored in your MySQL database library.
        </p>
        <button className="btn btn-steam btn-lg" onClick={onBrowseStore}>
          Explore Games
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Header & Search */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '16px',
        marginBottom: '24px',
      }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: 800, color: '#fff' }}>
            My Library ({library.length})
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            All persistent game licenses verified in MySQL database
          </p>
        </div>

        <div style={{ position: 'relative', width: '280px' }}>
          <span style={{ position: 'absolute', left: '12px', top: '10px', color: 'var(--text-secondary)' }}>
            <SearchIcon size={16} />
          </span>
          <input
            type="text"
            placeholder="Search owned games..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: '100%',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              padding: '8px 12px 8px 36px',
              color: '#fff',
              fontSize: '13px',
              outline: 'none',
            }}
          />
        </div>
      </div>

      {/* Library Grid */}
      <div className="games-grid">
        {filtered.map((game) => (
          <div
            key={game.id}
            className="glass-card"
            style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column' }}
            onClick={() => onSelectGame(game)}
          >
            {/* Artwork */}
            <div style={{ position: 'relative', width: '100%', paddingTop: '56.25%', overflow: 'hidden' }}>
              <img
                src={game.image_url}
                alt={game.title}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                }}
              />
              <div style={{
                position: 'absolute',
                top: '8px',
                right: '8px',
              }}>
                <span className="badge badge-owned" style={{ background: 'rgba(11, 14, 20, 0.85)', backdropFilter: 'blur(6px)' }}>
                  <CheckIcon size={12} style={{ marginRight: '4px' }} />
                  Purchased ✓
                </span>
              </div>
            </div>

            {/* Content */}
            <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', flex: 1 }}>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#fff', marginBottom: '4px' }}>
                {game.title}
              </h3>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                {game.genre} • ~{game.duration_hours}h
              </div>

              <div style={{
                marginTop: 'auto',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingTop: '12px',
                borderTop: '1px solid var(--border-color)',
              }}>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Ready to Play
                </span>

                <button
                  className={`btn btn-sm ${playingId === game.id ? 'btn-secondary' : 'btn-steam'}`}
                  onClick={(e) => handleLaunch(game.id, e)}
                >
                  <GamepadIcon size={14} />
                  {playingId === game.id ? 'Running... 🚀' : 'Play Now'}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
