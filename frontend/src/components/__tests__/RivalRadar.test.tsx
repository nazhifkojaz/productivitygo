import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import RivalRadar from '../RivalRadar';

describe('RivalRadar', () => {
    const mockBattle = {
        rival: {
            avatar_emoji: '🐉',
            username: 'DragonSlayer',
            level: 5,
            rank: 'SILVER',
            tasks_completed: 3,
            tasks_total: 5,
        },
    };

    describe('rendering', () => {
        it('renders rival username', () => {
            render(<RivalRadar battle={mockBattle} />);
            expect(screen.getByText('VS DragonSlayer')).toBeInTheDocument();
        });

        it('renders rival avatar emoji', () => {
            render(<RivalRadar battle={mockBattle} />);
            expect(screen.getByText('🐉')).toBeInTheDocument();
        });

        it('renders rival level and rank', () => {
            render(<RivalRadar battle={mockBattle} />);
            expect(screen.getByText('LVL 5 · SILVER')).toBeInTheDocument();
        });

        it('renders task progress', () => {
            render(<RivalRadar battle={mockBattle} />);
            expect(screen.getByText('3/5 TASKS')).toBeInTheDocument();
        });

        it('renders progress bar with correct width', () => {
            const { container } = render(<RivalRadar battle={mockBattle} />);
            const progressBar = container.querySelector('[style]');
            expect(progressBar).toHaveStyle({ width: '60%' });
        });
    });

    describe('defaults', () => {
        it('uses default values when rival fields are missing', () => {
            render(<RivalRadar battle={{ rival: {} }} />);
            expect(screen.getByText('VS Rival')).toBeInTheDocument();
            expect(screen.getByText('😈')).toBeInTheDocument();
            expect(screen.getByText('LVL 1 · BRONZE')).toBeInTheDocument();
            expect(screen.getByText('0/0 TASKS')).toBeInTheDocument();
        });

        it('handles undefined rival gracefully', () => {
            render(<RivalRadar battle={{ rival: undefined }} />);
            expect(screen.getByText('VS Rival')).toBeInTheDocument();
        });
    });
});
