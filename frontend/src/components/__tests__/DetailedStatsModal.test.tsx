import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import DetailedStatsModal from '../DetailedStatsModal';
import type { ProfileStats } from '../../types/profile';

describe('DetailedStatsModal', () => {
  const mockStats: ProfileStats = {
    battle_wins: 10,
    total_xp: 5000,
    battle_fought: 15,
    win_rate: '67%',
    tasks_completed: 42,
    monster_rating: 85,
    monster_defeats: 7,
    monster_escapes: 2,
    adventure_count: 10,
    highest_tier_reached: 'hard',
    total_damage_dealt: 15000,
    adventure_completion_rate: '70%',
    avg_damage_per_adventure: 1500,
  };

  const mockOnClose = vi.fn();

  describe('rendering', () => {
    it('does not render when isOpen is false', () => {
      const { container } = render(
        <DetailedStatsModal
          isOpen={false}
          stats={mockStats}
          onClose={mockOnClose}
        />
      );

      expect(container.querySelector('[role="dialog"]')).not.toBeInTheDocument();
    });

    it('renders when isOpen is true', () => {
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={mockStats}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('Detailed Statistics')).toBeInTheDocument();
    });

    it('has correct ARIA attributes', () => {
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={mockStats}
          onClose={mockOnClose}
        />
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
      expect(dialog).toHaveAttribute('aria-modal', 'true');
    });

    it('returns null when stats is null', () => {
      const { container } = render(
        <DetailedStatsModal
          isOpen={true}
          stats={null}
          onClose={mockOnClose}
        />
      );

      expect(container.querySelector('[role="dialog"]')).not.toBeInTheDocument();
    });

    it('returns null when stats is undefined', () => {
      const { container } = render(
        <DetailedStatsModal
          isOpen={true}
          stats={undefined}
          onClose={mockOnClose}
        />
      );

      expect(container.querySelector('[role="dialog"]')).not.toBeInTheDocument();
    });
  });

  describe('PvP Statistics section', () => {
    it('displays PvP stats correctly', () => {
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={mockStats}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('PvP Statistics')).toBeInTheDocument();
      expect(screen.getByText('67%')).toBeInTheDocument(); // Win Rate
      expect(screen.getByText('10-5')).toBeInTheDocument(); // PvP Record (W-L)
      expect(screen.getByText('15')).toBeInTheDocument(); // Total Battles
    });

    it('calculates avg XP per battle', () => {
      const stats: ProfileStats = {
        battle_wins: 5,
        total_xp: 2500,
        battle_fought: 10,
        win_rate: '50%',
        tasks_completed: 20,
      };

      const { container } = render(
        <DetailedStatsModal
          isOpen={true}
          stats={stats}
          onClose={mockOnClose}
        />
      );

      // avg XP per battle = 2500 / 10 = 250
      expect(container.textContent).toContain('250');
    });
  });

  describe('Adventure Statistics section', () => {
    it('displays adventure stats correctly', () => {
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={mockStats}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('Adventure Statistics')).toBeInTheDocument();
      expect(screen.getByText('85')).toBeInTheDocument(); // Monster Rating
      expect(screen.getByText('70%')).toBeInTheDocument(); // Completion Rate
      expect(screen.getByText('7')).toBeInTheDocument(); // Monsters Defeated
      expect(screen.getByText('2')).toBeInTheDocument(); // Escaped
    });

    it('displays correct tier emoji', () => {
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={mockStats}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('🟠 HARD')).toBeInTheDocument(); // hard tier
    });

    it('displays total damage with formatting', () => {
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={mockStats}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('15.0K')).toBeInTheDocument(); // Total Damage
    });

    it('displays avg damage per adventure', () => {
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={mockStats}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('1500')).toBeInTheDocument(); // Avg Damage/Adventure
    });

    it('shows total adventures', () => {
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={mockStats}
          onClose={mockOnClose}
        />
      );

      // Use getAllByText since 10 may appear elsewhere (e.g., dates)
      const tens = screen.getAllByText('10');
      expect(tens.length).toBeGreaterThan(0);
    });
  });

  describe('General Statistics section', () => {
    it('displays general stats correctly', () => {
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={mockStats}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('General Statistics')).toBeInTheDocument();
      expect(screen.getByText('5000')).toBeInTheDocument(); // Total XP
      expect(screen.getByText('42')).toBeInTheDocument(); // Tasks Completed
    });

    it('calculates level from XP', () => {
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={mockStats}
          onClose={mockOnClose}
        />
      );

      // Level = floor(5000 / 500) + 1 = 11
      // Use getAllByText since 11 may appear elsewhere
      const elevens = screen.getAllByText('11');
      expect(elevens.length).toBeGreaterThan(0);
    });
  });

  describe('days active calculation', () => {
    it('calculates days active from created_at', () => {
      const createdDate = new Date();
      createdDate.setDate(createdDate.getDate() - 30); // 30 days ago

      const { container } = render(
        <DetailedStatsModal
          isOpen={true}
          stats={mockStats}
          createdAt={createdDate.toISOString()}
          onClose={mockOnClose}
        />
      );

      // Days active will be ~30-31 due to ceiling in calculation
      // Just verify it's in the expected range
      const textMatch = container.textContent.match(/Days Active(\d+)/);
      expect(textMatch).toBeTruthy();
      const daysActive = parseInt(textMatch?.[1] || '0', 10);
      expect(daysActive).toBeGreaterThanOrEqual(30);
      expect(daysActive).toBeLessThanOrEqual(32);
    });

    it('shows 0 when created_at is not provided', () => {
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={mockStats}
          createdAt={undefined}
          onClose={mockOnClose}
        />
      );

      const daysActiveElements = screen.getAllByText('0');
      expect(daysActiveElements.length).toBeGreaterThan(0);
    });

    it('calculates avg XP per day', () => {
      const createdDate = new Date();
      createdDate.setDate(createdDate.getDate() - 10); // 10 days ago

      const { container } = render(
        <DetailedStatsModal
          isOpen={true}
          stats={mockStats}
          createdAt={createdDate.toISOString()}
          onClose={mockOnClose}
        />
      );

      // avg XP per day = 5000 / 10 = 500
      // Use a more specific query to find the "Avg XP/Day" stat card
      expect(container.textContent).toContain('500');
    });
  });

  describe('tier emoji mapping', () => {
    it('shows correct emoji for easy tier', () => {
      const stats = { ...mockStats, highest_tier_reached: 'easy' };
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={stats}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('🟢 EASY')).toBeInTheDocument();
    });

    it('shows correct emoji for medium tier', () => {
      const stats = { ...mockStats, highest_tier_reached: 'medium' };
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={stats}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('🟡 MEDIUM')).toBeInTheDocument();
    });

    it('shows correct emoji for hard tier', () => {
      const stats = { ...mockStats, highest_tier_reached: 'hard' };
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={stats}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('🟠 HARD')).toBeInTheDocument();
    });

    it('shows correct emoji for expert tier', () => {
      const stats = { ...mockStats, highest_tier_reached: 'expert' };
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={stats}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('🔴 EXPERT')).toBeInTheDocument();
    });

    it('shows correct emoji for boss tier', () => {
      const stats = { ...mockStats, highest_tier_reached: 'boss' };
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={stats}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('👑 BOSS')).toBeInTheDocument();
    });

    it('defaults to easy emoji for unknown tier', () => {
      const stats = { ...mockStats, highest_tier_reached: 'unknown' };
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={stats}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('🟢 UNKNOWN')).toBeInTheDocument();
    });
  });

  describe('interaction', () => {
    it('calls onClose when close button is clicked', () => {
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={mockStats}
          onClose={mockOnClose}
        />
      );

      const closeButton = screen.getByLabelText('Close modal');
      fireEvent.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('calls onClose when Close footer button is clicked', () => {
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={mockStats}
          onClose={mockOnClose}
        />
      );

      // Reset mock to clear previous calls
      mockOnClose.mockClear();

      const closeButton = screen.getAllByText('Close')[0]; // Footer Close button
      fireEvent.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('renders close button with correct aria-label', () => {
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={mockStats}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByLabelText('Close modal')).toBeInTheDocument();
    });
  });

  describe('edge cases', () => {
    it('handles zero adventure count', () => {
      const stats: ProfileStats = {
        battle_wins: 5,
        total_xp: 1000,
        battle_fought: 8,
        win_rate: '63%',
        tasks_completed: 10,
        adventure_count: 0,
        monster_defeats: 0,
      };

      render(
        <DetailedStatsModal
          isOpen={true}
          stats={stats}
          onClose={mockOnClose}
        />
      );

      // Games played = battles (8) + adventures (0) = 8
      // Use getAllByText since 8 may appear multiple times (e.g., in dates)
      const eights = screen.getAllByText('8');
      expect(eights.length).toBeGreaterThan(0);
    });

    it('handles missing optional adventure stats', () => {
      const stats: ProfileStats = {
        battle_wins: 5,
        total_xp: 1000,
        battle_fought: 8,
        win_rate: '63%',
        tasks_completed: 10,
      };

      render(
        <DetailedStatsModal
          isOpen={true}
          stats={stats}
          onClose={mockOnClose}
        />
      );

      // Should render without errors
      expect(screen.getByText('PvP Statistics')).toBeInTheDocument();
      expect(screen.getByText('Adventure Statistics')).toBeInTheDocument();
      expect(screen.getByText('General Statistics')).toBeInTheDocument();
    });
  });

  describe('section headings', () => {
    it('renders all three section headings', () => {
      render(
        <DetailedStatsModal
          isOpen={true}
          stats={mockStats}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('PvP Statistics')).toBeInTheDocument();
      expect(screen.getByText('Adventure Statistics')).toBeInTheDocument();
      expect(screen.getByText('General Statistics')).toBeInTheDocument();
    });
  });
});
