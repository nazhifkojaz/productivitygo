import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ProfileStats from '../ProfileStats';

describe('ProfileStats', () => {
  describe('with null/undefined stats', () => {
    it('renders all stat cards with zero values when stats is null', () => {
      render(<ProfileStats stats={null} />);

      expect(screen.getAllByText('0')).toHaveLength(4);
    });

    it('renders all stat cards with zero values when stats is undefined', () => {
      render(<ProfileStats stats={undefined} />);

      expect(screen.getAllByText('0')).toHaveLength(4);
    });

    it('renders without stats prop', () => {
      render(<ProfileStats />);

      expect(screen.getAllByText('0')).toHaveLength(4);
    });
  });

  describe('with full stats', () => {
    it('displays all stat values correctly', () => {
      const stats = {
        battle_wins: 10,
        total_xp: 2500,
        battle_fought: 15,
        tasks_completed: 42,
      };

      render(<ProfileStats stats={stats} />);

      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('2500')).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument();
    });

    it('displays all stat labels', () => {
      render(<ProfileStats stats={{}} />);

      expect(screen.getByText('WINS')).toBeInTheDocument();
      expect(screen.getByText('TOTAL XP')).toBeInTheDocument();
      expect(screen.getByText('BATTLES')).toBeInTheDocument();
      expect(screen.getByText('TASKS')).toBeInTheDocument();
    });
  });

  describe('with partial stats', () => {
    it('shows provided values and zeros for missing fields', () => {
      const stats = {
        battle_wins: 5,
      };

      render(<ProfileStats stats={stats} />);

      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getAllByText('0')).toHaveLength(3);
    });

    it('handles zero values correctly', () => {
      const stats = {
        battle_wins: 0,
        total_xp: 0,
        battle_fought: 0,
        tasks_completed: 0,
      };

      render(<ProfileStats stats={stats} />);

      const zeros = screen.getAllByText('0');
      expect(zeros.length).toBe(4);
    });
  });

  describe('styling and structure', () => {
    it('applies custom className when provided', () => {
      const { container } = render(<ProfileStats stats={null} className="custom-class" />);

      const grid = container.querySelector('.custom-class');
      expect(grid).toBeInTheDocument();
    });

    it('renders the correct grid structure', () => {
      const { container } = render(<ProfileStats stats={null} />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('grid-cols-2', 'md:grid-cols-4');
    });

    it('uses Design 1 colors for stat cards', () => {
      const { container } = render(<ProfileStats stats={null} />);

      // Check for hard shadows and borders using more lenient selectors
      const statCards = container.querySelectorAll('.border-3');
      expect(statCards.length).toBeGreaterThanOrEqual(4);

      // Check that cards have the border-black class
      const blackBorders = container.querySelectorAll('.border-black');
      expect(blackBorders.length).toBeGreaterThanOrEqual(4);
    });
  });

  describe('edge cases', () => {
    it('handles very large numbers', () => {
      const stats = {
        battle_wins: 999999,
        total_xp: 1000000,
      };

      render(<ProfileStats stats={stats} />);

      expect(screen.getByText('999999')).toBeInTheDocument();
      expect(screen.getByText('1000000')).toBeInTheDocument();
    });
  });
});
