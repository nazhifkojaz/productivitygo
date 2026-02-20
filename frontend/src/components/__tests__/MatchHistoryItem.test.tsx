import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import MatchHistoryItem from '../MatchHistoryItem';
import type { MatchHistory } from '../../types/profile';

describe('MatchHistoryItem', () => {
    const baseMatch: MatchHistory = {
        id: '1',
        date: '2024-01-15',
        rival: 'TestUser',
        result: 'WIN',
        duration: 5,
        type: 'adventure',
    };

    describe('rendering variants', () => {
        it('renders full-size match history item', () => {
            render(<MatchHistoryItem match={baseMatch} />);
            expect(screen.getByText('VS TestUser')).toBeInTheDocument();
            expect(screen.getByText('WIN')).toBeInTheDocument();
        });

        it('renders compact variant', () => {
            const { container } = render(<MatchHistoryItem match={baseMatch} compact />);
            expect(container.querySelector('.p-3')).toBeInTheDocument();
            expect(container.querySelector('.text-sm')).toBeInTheDocument();
        });

        it('renders adventure with VS prefix', () => {
            const adventureMatch: MatchHistory = { ...baseMatch, type: 'adventure' };
            render(<MatchHistoryItem match={adventureMatch} />);
            expect(screen.getByText('VS TestUser')).toBeInTheDocument();
        });

        it('renders battle without VS prefix', () => {
            const battleMatch: MatchHistory = { ...baseMatch, type: 'battle' };
            render(<MatchHistoryItem match={battleMatch} />);
            expect(screen.getByText('TestUser')).toBeInTheDocument();
            expect(screen.queryByText('VS TestUser')).not.toBeInTheDocument();
        });

        it('renders emoji when provided', () => {
            const matchWithEmoji: MatchHistory = { ...baseMatch, emoji: '👹' };
            render(<MatchHistoryItem match={matchWithEmoji} />);
            expect(screen.getByText('👹')).toBeInTheDocument();
        });

        it('renders default sword emoji when none provided', () => {
            render(<MatchHistoryItem match={baseMatch} />);
            expect(screen.getByText('⚔️')).toBeInTheDocument();
        });
    });

    describe('result colors', () => {
        it('shows teal badge for WIN result', () => {
            const { container } = render(<MatchHistoryItem match={{ ...baseMatch, result: 'WIN' }} />);
            expect(container.querySelector('.bg-\\[\\#2A9D8F\\]')).toBeInTheDocument();
        });

        it('shows red badge for LOSS result', () => {
            const { container } = render(<MatchHistoryItem match={{ ...baseMatch, result: 'LOSS' }} />);
            expect(container.querySelector('.bg-\\[\\#E63946\\]')).toBeInTheDocument();
        });

        it('shows orange badge for ESCAPED result', () => {
            const { container } = render(<MatchHistoryItem match={{ ...baseMatch, result: 'ESCAPED' }} />);
            expect(container.querySelector('.bg-\\[\\#F4A261\\]')).toBeInTheDocument();
        });

        it('shows blue badge for COMPLETED result', () => {
            const { container } = render(<MatchHistoryItem match={{ ...baseMatch, result: 'COMPLETED' }} />);
            expect(container.querySelector('.bg-\\[\\#457B9D\\]')).toBeInTheDocument();
        });

        it('shows gray badge for DRAW result', () => {
            const { container } = render(<MatchHistoryItem match={{ ...baseMatch, result: 'DRAW' }} />);
            expect(container.querySelector('.bg-gray-400')).toBeInTheDocument();
        });

        it('shows gray fallback badge for unknown result', () => {
            const { container } = render(<MatchHistoryItem match={{ ...baseMatch, result: 'UNKNOWN' as any }} />);
            expect(container.querySelector('.bg-gray-300')).toBeInTheDocument();
        });
    });

    describe('conditional display', () => {
        it('shows duration when showDuration is true', () => {
            render(<MatchHistoryItem match={baseMatch} showDuration />);
            expect(screen.getByText(/5 DAYS/)).toBeInTheDocument();
        });

        it('hides duration when showDuration is false', () => {
            render(<MatchHistoryItem match={baseMatch} showDuration={false} />);
            expect(screen.queryByText(/DAYS/)).not.toBeInTheDocument();
        });

        it('shows XP when showXP is true and xp_earned is defined', () => {
            const matchWithXP: MatchHistory = { ...baseMatch, xp_earned: 100 };
            render(<MatchHistoryItem match={matchWithXP} showXP />);
            expect(screen.getByText(/\+100 XP/)).toBeInTheDocument();
        });

        it('hides XP when showXP is false', () => {
            const matchWithXP: MatchHistory = { ...baseMatch, xp_earned: 100 };
            render(<MatchHistoryItem match={matchWithXP} showXP={false} />);
            expect(screen.queryByText(/XP/)).not.toBeInTheDocument();
        });

        it('hides XP when xp_earned is undefined', () => {
            render(<MatchHistoryItem match={baseMatch} showXP />);
            expect(screen.queryByText(/XP/)).not.toBeInTheDocument();
        });
    });

    describe('accessibility', () => {
        it('has semantic article tag', () => {
            const { container } = render(<MatchHistoryItem match={baseMatch} />);
            expect(container.querySelector('article')).toBeInTheDocument();
        });

        it('has time element with dateTime attribute', () => {
            const { container } = render(<MatchHistoryItem match={baseMatch} />);
            const timeEl = container.querySelector('time');
            expect(timeEl).toBeInTheDocument();
            expect(timeEl).toHaveAttribute('dateTime', '2024-01-15');
        });

        it('has aria-label on result badge', () => {
            const { container } = render(<MatchHistoryItem match={baseMatch} />);
            const resultBadge = container.querySelector('[aria-label="Result: WIN"]');
            expect(resultBadge).toBeInTheDocument();
        });

        it('has emoji with aria-hidden', () => {
            const { container } = render(<MatchHistoryItem match={baseMatch} />);
            const emoji = container.querySelector('[aria-hidden="true"]');
            expect(emoji).toBeInTheDocument();
        });
    });

    describe('edge cases', () => {
        it('handles missing date gracefully', () => {
            const { container } = render(<MatchHistoryItem match={{ ...baseMatch, date: '' }} />);
            expect(screen.getByText('Unknown date')).toBeInTheDocument();
        });

        it('handles invalid date gracefully', () => {
            const { container } = render(<MatchHistoryItem match={{ ...baseMatch, date: 'invalid' }} />);
            expect(screen.getByText('Unknown date')).toBeInTheDocument();
        });

        it('handles missing duration', () => {
            const matchWithoutDuration: MatchHistory = { ...baseMatch, duration: undefined as any };
            render(<MatchHistoryItem match={matchWithoutDuration} />);
            expect(screen.queryByText(/DAYS/)).not.toBeInTheDocument();
        });

        it('handles zero duration', () => {
            render(<MatchHistoryItem match={{ ...baseMatch, duration: 0 }} />);
            expect(screen.getByText(/0 DAYS/)).toBeInTheDocument();
        });

        it('handles zero XP', () => {
            const matchWithZeroXP: MatchHistory = { ...baseMatch, xp_earned: 0 };
            render(<MatchHistoryItem match={matchWithZeroXP} />);
            expect(screen.getByText(/\+0 XP/)).toBeInTheDocument();
        });
    });
});
