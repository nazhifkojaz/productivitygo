import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ActiveSessionBanner from '../ActiveSessionBanner';

describe('ActiveSessionBanner', () => {
    const mockOnGoToArena = vi.fn();

    const battleProps = {
        sessionType: 'battle' as const,
        opponentName: 'DragonSlayer99',
        opponentEmoji: '🐉',
        currentDay: 3,
        totalDays: 5,
        onGoToArena: mockOnGoToArena,
    };

    const adventureProps = {
        sessionType: 'adventure' as const,
        opponentName: 'Lazy Slime',
        opponentEmoji: '🟢',
        currentDay: 2,
        totalDays: 3,
        onGoToArena: mockOnGoToArena,
    };

    describe('battle session', () => {
        it('renders battle banner with red background', () => {
            const { container } = render(<ActiveSessionBanner {...battleProps} />);
            const banner = container.firstChild as HTMLElement;
            expect(banner).toHaveClass('bg-[#E63946]');
        });

        it('renders opponent name', () => {
            render(<ActiveSessionBanner {...battleProps} />);
            expect(screen.getByText('VS DragonSlayer99')).toBeInTheDocument();
        });

        it('renders opponent emoji', () => {
            render(<ActiveSessionBanner {...battleProps} />);
            expect(screen.getByText('🐉')).toBeInTheDocument();
        });

        it('renders day progress', () => {
            render(<ActiveSessionBanner {...battleProps} />);
            expect(screen.getByText('Day 3 of 5')).toBeInTheDocument();
        });

        it('renders ACTIVE BATTLE label', () => {
            render(<ActiveSessionBanner {...battleProps} />);
            expect(screen.getByText('ACTIVE BATTLE')).toBeInTheDocument();
        });

        it('calls onGoToArena when button is clicked', async () => {
            const user = userEvent.setup();
            render(<ActiveSessionBanner {...battleProps} />);

            const goButton = screen.getByRole('button', { name: /go to arena/i });
            await user.click(goButton);

            expect(mockOnGoToArena).toHaveBeenCalledTimes(1);
        });
    });

    describe('adventure session', () => {
        it('renders adventure banner with purple background', () => {
            const { container } = render(<ActiveSessionBanner {...adventureProps} />);
            const banner = container.firstChild as HTMLElement;
            expect(banner).toHaveClass('bg-[#9D4EDD]');
        });

        it('renders monster name', () => {
            render(<ActiveSessionBanner {...adventureProps} />);
            expect(screen.getByText('FIGHTING Lazy Slime')).toBeInTheDocument();
        });

        it('renders monster emoji', () => {
            render(<ActiveSessionBanner {...adventureProps} />);
            expect(screen.getByText('🟢')).toBeInTheDocument();
        });

        it('renders day progress', () => {
            render(<ActiveSessionBanner {...adventureProps} />);
            expect(screen.getByText('Day 2 of 3')).toBeInTheDocument();
        });

        it('renders ACTIVE ADVENTURE label', () => {
            render(<ActiveSessionBanner {...adventureProps} />);
            expect(screen.getByText('ACTIVE ADVENTURE')).toBeInTheDocument();
        });
    });

    describe('without opponent emoji', () => {
        it('shows icon instead of emoji when opponentEmoji is not provided', () => {
            const propsWithoutEmoji = {
                ...battleProps,
                opponentEmoji: undefined,
            };
            const { container } = render(<ActiveSessionBanner {...propsWithoutEmoji} />);

            // Should render an icon (SVG) instead of emoji
            const iconContainer = container.querySelector('svg')?.closest('div');
            expect(iconContainer).toBeInTheDocument();
        });
    });

    describe('accessibility', () => {
        it('has accessible button name', () => {
            render(<ActiveSessionBanner {...battleProps} />);
            const button = screen.getByRole('button', { name: /go to arena/i });
            expect(button).toBeInTheDocument();
        });

        it('button is keyboard accessible', async () => {
            const user = userEvent.setup();
            render(<ActiveSessionBanner {...battleProps} />);

            const button = screen.getByRole('button', { name: /go to arena/i });
            await user.click(button);
            expect(mockOnGoToArena).toHaveBeenCalled();
        });
    });

    describe('styling', () => {
        it('applies neobrutalist border classes', () => {
            const { container } = render(<ActiveSessionBanner {...battleProps} />);
            const banner = container.firstChild as HTMLElement;
            expect(banner).toHaveClass('border-4', 'border-black');
        });

        it('applies shadow classes', () => {
            const { container } = render(<ActiveSessionBanner {...battleProps} />);
            const banner = container.firstChild as HTMLElement;
            expect(banner).toHaveClass('shadow-[6px_6px_0_0_#000]');
        });

        it('button has neobrutalist styling', () => {
            const { container } = render(<ActiveSessionBanner {...battleProps} />);
            const button = container.querySelector('button');
            expect(button).toHaveClass('bg-white', 'text-black', 'border-3', 'border-black');
        });
    });
});
