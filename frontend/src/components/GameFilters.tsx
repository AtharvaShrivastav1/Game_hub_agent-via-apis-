import React from 'react';
import { SearchIcon } from './Icons';

interface GameFiltersProps {
  genres: string[];
  selectedGenre: string;
  onSelectGenre: (genre: string) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  maxPrice: number | null;
  onMaxPriceChange: (price: number | null) => void;
  maxDuration: number | null;
  onMaxDurationChange: (duration: number | null) => void;
  sortBy: string;
  onSortByChange: (sort: string) => void;
}

export const GameFilters: React.FC<GameFiltersProps> = ({
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
}) => {
  return (
    <div style={{ marginBottom: '28px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Search and Secondary Filter Row */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '12px',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        {/* Search Bar */}
        <div style={{
          position: 'relative',
          flex: '1 1 320px',
          maxWidth: '480px',
        }}>
          <span style={{
            position: 'absolute',
            left: '14px',
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--text-secondary)',
            pointerEvents: 'none',
          }}>
            <SearchIcon size={18} />
          </span>
          <input
            type="text"
            placeholder="Search by title, genre, developer..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            style={{
              width: '100%',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              padding: '11px 16px 11px 42px',
              color: '#fff',
              fontSize: '14px',
              outline: 'none',
              transition: 'border-color 0.2s',
            }}
            onFocus={(e) => (e.currentTarget.style.borderColor = 'var(--steam-blue)')}
            onBlur={(e) => (e.currentTarget.style.borderColor = 'var(--border-color)')}
          />
        </div>

        {/* Dropdowns: Price, Duration, Sorting */}
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Price Filter */}
          <select
            value={maxPrice !== null ? maxPrice.toString() : ''}
            onChange={(e) => onMaxPriceChange(e.target.value ? Number(e.target.value) : null)}
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              color: 'var(--text-primary)',
              padding: '8px 12px',
              fontSize: '13px',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="">All Budgets</option>
            <option value="500">Under ₹500</option>
            <option value="1000">Under ₹1,000</option>
            <option value="1500">Under ₹1,500</option>
            <option value="2000">Under ₹2,000</option>
            <option value="3000">Under ₹3,000</option>
          </select>

          {/* Duration Filter */}
          <select
            value={maxDuration !== null ? maxDuration.toString() : ''}
            onChange={(e) => onMaxDurationChange(e.target.value ? Number(e.target.value) : null)}
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              color: 'var(--text-primary)',
              padding: '8px 12px',
              fontSize: '13px',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="">Any Playtime</option>
            <option value="20">Under 20 Hours (Short)</option>
            <option value="40">Under 40 Hours (Medium)</option>
            <option value="80">Under 80 Hours (Long)</option>
          </select>

          {/* Sort By */}
          <select
            value={sortBy}
            onChange={(e) => onSortByChange(e.target.value)}
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              color: 'var(--text-primary)',
              padding: '8px 12px',
              fontSize: '13px',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="rating_desc">Highest Rated ⭐</option>
            <option value="price_asc">Price: Low to High</option>
            <option value="price_desc">Price: High to Low</option>
            <option value="duration_asc">Playtime: Shortest First</option>
          </select>
        </div>
      </div>

      {/* Genre Pills */}
      <div style={{
        display: 'flex',
        gap: '8px',
        overflowX: 'auto',
        paddingBottom: '4px',
        scrollbarWidth: 'none',
      }}>
        <button
          className={`btn btn-sm ${selectedGenre === 'All' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: '16px' }}
          onClick={() => onSelectGenre('All')}
        >
          All Genres
        </button>
        {genres.map((g) => (
          <button
            key={g}
            className={`btn btn-sm ${selectedGenre === g ? 'btn-primary' : 'btn-secondary'}`}
            style={{ borderRadius: '16px' }}
            onClick={() => onSelectGenre(g)}
          >
            {g}
          </button>
        ))}
      </div>
    </div>
  );
};
