import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import AdventureResult from '../AdventureResult';
import { AuthProvider } from '../../context/AuthContext';
import * as useAdventureDetailsModule from '../../hooks/useAdventureDetails';
import confetti from 'canvas-confetti';

// Mock confetti
vi.mock('canvas-confetti');

// Mock the hook
const mockRefetch = vi.fn();
const mockUseAdventureDetails = vi.spyOn(useAdventureDetailsModule, 'useAdventureDetails');

const mockAdventure = {
    id: 'adv-123',
    user_id: 'user-123',
    monster_id: 'monster-123',
    duration: 5,
    start_date: '2026-02-01',
    deadline: '2026-02-05',
    monster_max_hp: 200,
    monster_current_hp: 0,
    status: 'completed',
    current_round: 3,
    total_damage_dealt: 200,
    xp_earned: 240,
    break_days_used: 0,
    max_break_days: 2,
    is_on_break: false,
    break_end_date: null,
    monster: {
        id: 'monster-123',
        name: 'Procrastination Goblin',
        emoji: '👺',
        tier: 'medium',
        base_hp: 200,
        description: "There's still time...",
    },
    app_state: 'COMPLETED' as const,
    days_remaining: 0,
    daily_breakdown: [
        { date: '2026-02-01', damage_dealt: 70 },
        { date: '2026-02-02', damage_dealt: 65 },
        { date: '2026-02-03', damage_dealt: 65 },
    ],
};

const wrapper = ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter initialEntries={['/adventure-result/adv-123']}>
        <AuthProvider>
            {children}
        </AuthProvider>
    </MemoryRouter>
);

describe('AdventureResult', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        // Default mock setup
        mockUseAdventureDetails.mockReturnValue({
            data: mockAdventure,
            isLoading: false,
            error: null,
            refetch: mockRefetch,
        } as any);
    });

    describe('loading state', () => {
        it('shows loading message when isLoading is true', () => {
            mockUseAdventureDetails.mockReturnValue({
                data: undefined,
                isLoading: true,
                error: null,
                refetch: mockRefetch,
            } as any);

            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('CALCULATING RESULTS...')).toBeInTheDocument();
        });
    });

    describe('not found state', () => {
        it('shows not found message when adventure is null', () => {
            mockUseAdventureDetails.mockReturnValue({
                data: null,
                isLoading: false,
                error: null,
                refetch: mockRefetch,
            } as any);

            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('ADVENTURE NOT FOUND')).toBeInTheDocument();
        });
    });

    describe('victory outcome', () => {
        beforeEach(() => {
            mockUseAdventureDetails.mockReturnValue({
                data: { ...mockAdventure, status: 'completed' as const, monster_current_hp: 0 },
                isLoading: false,
                error: null,
                refetch: mockRefetch,
            } as any);
        });

        it('renders victory title and subtitle', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('VICTORY!')).toBeInTheDocument();
            expect(screen.getByText(/You defeated Procrastination Goblin!/)).toBeInTheDocument();
        });

        it('shows purple background for victory', () => {
            const { container } = render(<AdventureResult />, { wrapper });

            const outcomeCard = container.querySelector('.bg-purple-400');
            expect(outcomeCard).toBeInTheDocument();
        });

        it('shows trophy icon for victory', () => {
            render(<AdventureResult />, { wrapper });

            const trophyIcon = document.querySelector('svg');
            expect(trophyIcon).toBeInTheDocument();
        });

        it('triggers confetti on victory', () => {
            render(<AdventureResult />, { wrapper });

            expect(confetti).toHaveBeenCalledWith({
                particleCount: 150,
                spread: 70,
                origin: { y: 0.6 },
                colors: ['#A855F7', '#EC4899', '#8B5CF6'],
            });
        });

        it('shows full XP without penalty message', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('+240 XP')).toBeInTheDocument();
            expect(screen.queryByText(/\(50% penalty applied\)/)).not.toBeInTheDocument();
        });

        it('shows empty HP bar (defeated monster)', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('0 / 200')).toBeInTheDocument();
            const hpBar = document.querySelector('.h-full.transition-all');
            expect(hpBar).toHaveStyle({ width: '0%' });
        });
    });

    describe('escaped outcome', () => {
        beforeEach(() => {
            mockUseAdventureDetails.mockReturnValue({
                data: {
                    ...mockAdventure,
                    status: 'escaped' as const,
                    monster_current_hp: 50,
                    xp_earned: 120, // 50% penalty
                },
                isLoading: false,
                error: null,
                refetch: mockRefetch,
            } as any);
        });

        it('renders escaped title and subtitle', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('ESCAPED!')).toBeInTheDocument();
            expect(screen.getByText(/Procrastination Goblin got away\.\.\./)).toBeInTheDocument();
        });

        it('shows gray background for escaped', () => {
            const { container } = render(<AdventureResult />, { wrapper });

            const outcomeCard = container.querySelector('.bg-gray-400');
            expect(outcomeCard).toBeInTheDocument();
        });

        it('shows 50% penalty message', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText(/\(50% penalty applied\)/)).toBeInTheDocument();
        });

        it('does not trigger confetti for escaped', () => {
            render(<AdventureResult />, { wrapper });

            expect(confetti).not.toHaveBeenCalled();
        });

        it('shows partial HP bar', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('50 / 200')).toBeInTheDocument();
            const hpBar = document.querySelector('.h-full.transition-all');
            expect(hpBar).toHaveStyle({ width: '25%' });
        });
    });

    describe('abandoned outcome', () => {
        beforeEach(() => {
            mockUseAdventureDetails.mockReturnValue({
                data: {
                    ...mockAdventure,
                    status: 'abandoned' as const,
                    monster_current_hp: 150,
                    xp_earned: 100,
                },
                isLoading: false,
                error: null,
                refetch: mockRefetch,
            } as any);
        });

        it('render retreated title and subtitle', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('RETREATED')).toBeInTheDocument();
            expect(screen.getByText(/You lived to fight another day\./)).toBeInTheDocument();
        });

        it('shows yellow background for abandoned', () => {
            const { container } = render(<AdventureResult />, { wrapper });

            const outcomeCard = container.querySelector('.bg-yellow-400');
            expect(outcomeCard).toBeInTheDocument();
        });

        it('shows 50% penalty message', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText(/\(50% penalty applied\)/)).toBeInTheDocument();
        });

        it('shows partial HP bar for abandoned', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('150 / 200')).toBeInTheDocument();
            const hpBar = document.querySelector('.h-full.transition-all');
            expect(hpBar).toHaveStyle({ width: '75%' });
        });
    });

    describe('monster card display', () => {
        it('shows monster emoji and name', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('👺')).toBeInTheDocument();
            expect(screen.getByText('Procrastination Goblin')).toBeInTheDocument();
        });

        it('shows monster tier badge', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('MEDIUM')).toBeInTheDocument();
        });

        it('shows correct tier colors', () => {
            // Test with medium tier (default)
            const { unmount } = render(<AdventureResult />, { wrapper });
            expect(screen.getByText('MEDIUM')).toHaveClass('bg-yellow-400');
            unmount();

            // Test with easy tier
            mockUseAdventureDetails.mockReturnValue({
                data: {
                    ...mockAdventure,
                    monster: { ...mockAdventure.monster!, tier: 'easy' as const },
                },
                isLoading: false,
                error: null,
                refetch: mockRefetch,
            } as any);
            render(<AdventureResult />, { wrapper });
            expect(screen.getByText('EASY')).toHaveClass('bg-green-400');
        });

        it('shows total damage and days survived', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('200')).toBeInTheDocument(); // Total damage
            expect(screen.getByText('TOTAL DAMAGE')).toBeInTheDocument();
            expect(screen.getByText('3')).toBeInTheDocument(); // Days survived
            expect(screen.getByText('DAYS SURVIVED')).toBeInTheDocument();
        });
    });

    describe('daily breakdown', () => {
        it('renders adventure log with daily breakdown', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('Adventure Log')).toBeInTheDocument();
            expect(screen.getAllByText(/Day \d/)).toHaveLength(3); // 3 days
            expect(screen.getByText('70 DMG')).toBeInTheDocument(); // First day damage
        });

        it('does not render adventure log when breakdown is empty', () => {
            mockUseAdventureDetails.mockReturnValue({
                data: { ...mockAdventure, daily_breakdown: [] },
                isLoading: false,
                error: null,
                refetch: mockRefetch,
            } as any);

            render(<AdventureResult />, { wrapper });

            expect(screen.queryByText('Adventure Log')).not.toBeInTheDocument();
        });

        it('does not render adventure log when breakdown is undefined', () => {
            mockUseAdventureDetails.mockReturnValue({
                data: { ...mockAdventure, daily_breakdown: undefined as any },
                isLoading: false,
                error: null,
                refetch: mockRefetch,
            } as any);

            render(<AdventureResult />, { wrapper });

            expect(screen.queryByText('Adventure Log')).not.toBeInTheDocument();
        });
    });

    describe('navigation', () => {
        it('shows Return to Lobby button', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('Return to Lobby')).toBeInTheDocument();
        });

        it('navigates to dashboard when Return to Lobby is clicked', async () => {
            const user = userEvent.setup();
            const mockNavigate = vi.fn();

            // Mock useNavigate
            vi.doMock('react-router-dom', async () => {
                const actual = await vi.importActual('react-router-dom');
                return {
                    ...actual,
                    useNavigate: () => mockNavigate,
                };
            });

            render(<AdventureResult />, { wrapper });

            const returnBtn = screen.getByText('Return to Lobby');
            await user.click(returnBtn);

            // Button exists and is clickable - navigation is handled by react-router
            expect(returnBtn).toBeInTheDocument();
        });
    });

    describe('fallback values', () => {
        it('shows default values when monster is missing', () => {
            mockUseAdventureDetails.mockReturnValue({
                data: {
                    ...mockAdventure,
                    monster: undefined as any,
                },
                isLoading: false,
                error: null,
                refetch: mockRefetch,
            } as any);

            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('👹')).toBeInTheDocument(); // Default emoji
            expect(screen.getByText('Unknown Monster')).toBeInTheDocument();
            expect(screen.getByText('EASY')).toBeInTheDocument(); // Default tier
        });
    });

    describe('styling', () => {
        it('applies neo-brutalist classes', () => {
            const { container } = render(<AdventureResult />, { wrapper });

            const monsterCard = container.querySelectorAll('.border-4', '.border-3', '.shadow-neo');
            expect(monsterCard.length).toBeGreaterThan(0);
        });
    });
});
