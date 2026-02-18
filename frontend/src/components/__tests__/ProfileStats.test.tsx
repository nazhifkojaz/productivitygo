import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ProfileStats from '../ProfileStats';

describe('ProfileStats', () => {
  describe('with null/undefined stats', () => {
    it('renders all stat cards with zero values when stats is null', () => {
      render(<ProfileStats stats={null} />);

      expect(screen.getAllByText('0')).toHaveLength(6);
    });

    it('renders all stat cards with zero values when stats is undefined', () => {
      render(<ProfileStats stats={undefined} />);

      expect(screen.getAllByText('0')).toHaveLength(6);
    });

    it('renders without stats prop', () => {
      render(<ProfileStats />);

      expect(screen.getAllByText('0')).toHaveLength(6);
    });
  });

  describe('with full stats', () => {
    it('displays all stat values correctly', () => {
      const stats = {
        battle_wins: 10,
        total_xp: 2500,
        tasks_completed: 42,
        monster_rating: 85,
        monster_defeats: 7,
        total_damage_dealt: 15000,
      };

      render(<ProfileStats stats={stats} />);

      expect(screen.getByText('10')).toBeInTheDocument(); // WINS
      expect(screen.getByText('2500')).toBeInTheDocument(); // TOTAL XP
      expect(screen.getByText('42')).toBeInTheDocument(); // TASKS
      expect(screen.getByText('85')).toBeInTheDocument(); // RATING
      expect(screen.getByText('7')).toBeInTheDocument(); // SLAIN
      expect(screen.getByText('15.0K')).toBeInTheDocument(); // DAMAGE (formatted)
    });

    it('displays all stat labels', () => {
      render(<ProfileStats stats={{}} />);

      expect(screen.getByText('WINS')).toBeInTheDocument();
      expect(screen.getByText('TOTAL XP')).toBeInTheDocument();
      expect(screen.getByText('TASKS')).toBeInTheDocument();
      expect(screen.getByText('RATING')).toBeInTheDocument();
      expect(screen.getByText('SLAIN')).toBeInTheDocument();
      expect(screen.getByText('DAMAGE')).toBeInTheDocument();
    });
  });

  describe('formatNumber helper', () => {
    it('formats thousands with K suffix', () => {
      const stats = { total_damage_dealt: 1500 };
      render(<ProfileStats stats={stats} />);

      expect(screen.getByText('1.5K')).toBeInTheDocument();
    });

    it('formats millions with M suffix', () => {
      const stats = { total_damage_dealt: 1500000 };
      render(<ProfileStats stats={stats} />);

      expect(screen.getByText('1.5M')).toBeInTheDocument();
    });

    it('displays 0 for zero damage', () => {
      const stats = { total_damage_dealt: 0 };
      render(<ProfileStats stats={stats} />);

      // Use getAllByText since there are multiple zeros on the page
      const zeros = screen.getAllByText('0');
      expect(zeros.length).toBeGreaterThan(0);
    });

    it('displays raw number for small values', () => {
      const stats = { total_damage_dealt: 500 };
      render(<ProfileStats stats={stats} />);

      expect(screen.getByText('500')).toBeInTheDocument();
    });
  });

  describe('with partial stats', () => {
    it('shows provided values and zeros for missing fields', () => {
      const stats = {
        battle_wins: 5,
        monster_rating: 75,
      };

      render(<ProfileStats stats={stats} />);

      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('75')).toBeInTheDocument();
      // Should have 4 zeros for: total_xp, tasks, monster_defeats, total_damage
      const zeros = screen.getAllByText('0');
      expect(zeros.length).toBeGreaterThanOrEqual(4);
    });

    it('handles zero values correctly', () => {
      const stats = {
        battle_wins: 0,
        total_xp: 0,
        tasks_completed: 0,
        monster_rating: 0,
        monster_defeats: 0,
        total_damage_dealt: 0,
      };

      render(<ProfileStats stats={stats} />);

      const zeros = screen.getAllByText('0');
      expect(zeros.length).toBeGreaterThanOrEqual(6);
    });
  });

  describe('new user with no adventure stats', () => {
    it('displays zero for all adventure stats', () => {
      const stats = {
        battle_wins: 3,
        total_xp: 500,
        battle_fought: 5,
        tasks_completed: 10,
      };

      render(<ProfileStats stats={stats} />);

      expect(screen.getByText('3')).toBeInTheDocument(); // WINS
      expect(screen.getByText('500')).toBeInTheDocument(); // TOTAL XP
      expect(screen.getByText('10')).toBeInTheDocument(); // TASKS
      // Adventure stats should show 0 - use getAllByText since zeros exist elsewhere
      const zeros = screen.getAllByText('0');
      expect(zeros.length).toBeGreaterThanOrEqual(3);
    });
  });

  describe('styling and structure', () => {
    it('applies custom className when provided', () => {
      const { container } = render(<ProfileStats stats={null} className="custom-class" />);

      const grid = container.querySelector('.custom-class');
      expect(grid).toBeInTheDocument();
    });

    it('renders the correct grid structure for 6-card layout', () => {
      const { container } = render(<ProfileStats stats={null} />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('grid-cols-2', 'md:grid-cols-3');
    });

    it('renders 6 stat cards', () => {
      const { container } = render(<ProfileStats stats={null} />);

      const statCards = container.querySelectorAll('.border-3');
      expect(statCards.length).toBeGreaterThanOrEqual(6);
    });

    it('has ARIA labels for accessibility', () => {
      const stats = {
        battle_wins: 10,
        monster_rating: 85,
      };

      render(<ProfileStats stats={stats} />);

      // Check for aria-label attributes
      const winsCard = screen.getByLabelText('PvP Battle Wins: 10');
      expect(winsCard).toBeInTheDocument();

      const ratingCard = screen.getByLabelText('Monster Rating: 85');
      expect(ratingCard).toBeInTheDocument();
    });
  });

  describe('edge cases', () => {
    it('handles very large numbers with formatting', () => {
      const stats = {
        battle_wins: 999999,
        total_xp: 1000000,
        total_damage_dealt: 2500000,
      };

      render(<ProfileStats stats={stats} />);

      expect(screen.getByText('999999')).toBeInTheDocument(); // WINS not formatted
      expect(screen.getByText('1000000')).toBeInTheDocument(); // XP not formatted
      expect(screen.getByText('2.5M')).toBeInTheDocument(); // DAMAGE formatted
    });

    it('handles undefined total_damage_dealt', () => {
      const stats = {
        battle_wins: 10,
      };

      render(<ProfileStats stats={stats} />);

      // DAMAGE shows 0 (use getAllByText since there are multiple zeros)
      const zeros = screen.getAllByText('0');
      expect(zeros.length).toBeGreaterThan(0);
    });
  });

  describe('adventure stats', () => {
    it('displays monster_rating correctly', () => {
      const stats = { monster_rating: 95 };
      render(<ProfileStats stats={stats} />);

      expect(screen.getByText('95')).toBeInTheDocument();
    });

    it('displays monster_defeats as SLAIN', () => {
      const stats = { monster_defeats: 12 };
      render(<ProfileStats stats={stats} />);

      expect(screen.getByText('12')).toBeInTheDocument();
      expect(screen.getByText('SLAIN')).toBeInTheDocument();
    });

    it('displays total_damage_dealt with formatting', () => {
      const stats = { total_damage_dealt: 12345 };
      render(<ProfileStats stats={stats} />);

      expect(screen.getByText('12.3K')).toBeInTheDocument();
    });
  });
});
