import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ProfileStats from '../ProfileStats';

describe('ProfileStats', () => {
  describe('with null/undefined stats', () => {
    it('renders all stat boxes with zero values when stats is null', () => {
      render(<ProfileStats stats={null} />);

      expect(screen.getAllByText('0')).toHaveLength(4); // 4 numeric stat boxes show 0
      expect(screen.getByText('0%')).toBeInTheDocument(); // Win rate shows 0%
    });

    it('renders all stat boxes with zero values when stats is undefined', () => {
      render(<ProfileStats stats={undefined} />);

      expect(screen.getAllByText('0')).toHaveLength(4); // 4 numeric stat boxes show 0
      expect(screen.getByText('0%')).toBeInTheDocument(); // Win rate shows 0%
    });

    it('renders without stats prop', () => {
      render(<ProfileStats />);

      expect(screen.getAllByText('0')).toHaveLength(4); // 4 numeric stat boxes show 0
      expect(screen.getByText('0%')).toBeInTheDocument(); // Win rate shows 0%
    });
  });

  describe('with full stats', () => {
    it('displays all stat values correctly', () => {
      const stats = {
        battle_wins: 10,
        total_xp: 2500,
        battle_fought: 15,
        win_rate: '67%',
        tasks_completed: 42,
      };

      render(<ProfileStats stats={stats} />);

      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('2500')).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument();
      expect(screen.getByText('67%')).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument();
    });

    it('displays all stat labels', () => {
      render(<ProfileStats stats={{}} />);

      expect(screen.getByText('Battle Wins')).toBeInTheDocument();
      expect(screen.getByText('Total XP')).toBeInTheDocument();
      expect(screen.getByText('Battle Fought')).toBeInTheDocument();
      expect(screen.getByText('Win Rate')).toBeInTheDocument();
      expect(screen.getByText('Tasks Completed')).toBeInTheDocument();
    });
  });

  describe('with partial stats', () => {
    it('shows provided values and zeros for missing fields', () => {
      const stats = {
        battle_wins: 5,
      };

      render(<ProfileStats stats={stats} />);

      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getAllByText('0')).toHaveLength(3); // total_xp, battle_fought, tasks_completed show 0
      expect(screen.getByText('0%')).toBeInTheDocument(); // Win rate default
    });

    it('handles zero values correctly', () => {
      const stats = {
        battle_wins: 0,
        total_xp: 0,
        battle_fought: 0,
        win_rate: '0%',
        tasks_completed: 0,
      };

      render(<ProfileStats stats={stats} />);

      const zeros = screen.getAllByText('0');
      expect(zeros.length).toBeGreaterThan(0);
      expect(screen.getByText('0%')).toBeInTheDocument();
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
      expect(grid).toHaveClass('grid-cols-2', 'md:grid-cols-3', 'gap-4', 'mt-8');
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

    it('handles string win rate formats', () => {
      const stats = {
        win_rate: '100%',
      };

      render(<ProfileStats stats={stats} />);

      expect(screen.getByText('100%')).toBeInTheDocument();
    });
  });
});
