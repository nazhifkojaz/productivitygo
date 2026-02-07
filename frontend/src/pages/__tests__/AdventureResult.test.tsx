import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import AdventureResult from '../AdventureResult';
import { AuthProvider } from '../../context/AuthContext';
import * as useAdventureDetailsModule from '../../hooks/useAdventureDetails';

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
        { date: '2026-02-01', damage_dealt: 70, tasks_completed: 3 },
        { date: '2026-02-02', damage_dealt: 65, tasks_completed: 2 },
        { date: '2026-02-03', damage_dealt: 65, tasks_completed: 3 },
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

            const outcomeCard = container.querySelector('.bg-\\[\\#9D4EDD\\]');
            expect(outcomeCard).toBeInTheDocument();
        });

        it('shows dragon icon for victory', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('🐉')).toBeInTheDocument();
        });

        it('shows full XP without penalty message', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText(/\+240/)).toBeInTheDocument();
            expect(screen.queryByText(/\(50% penalty applied\)/)).not.toBeInTheDocument();
        });

        it('shows monster card with black header bar', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('// MONSTER //')).toBeInTheDocument();
        });

        it('shows empty HP bar (defeated monster)', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('0 / 200')).toBeInTheDocument();
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

        it('shows partial HP bar', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('50 / 200')).toBeInTheDocument();
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

        it('renders retreated title and subtitle', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('RETREATED')).toBeInTheDocument();
            expect(screen.getByText(/You lived to fight another day\./)).toBeInTheDocument();
        });

        it('shows 50% penalty message', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText(/\(50% penalty applied\)/)).toBeInTheDocument();
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

        it('shows total damage and days survived', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('200')).toBeInTheDocument(); // Total damage
            expect(screen.getByText('Damage Dealt')).toBeInTheDocument();
            expect(screen.getByText('3')).toBeInTheDocument(); // Days survived
            expect(screen.getByText('Days Survived')).toBeInTheDocument();
        });

        it('shows HP with heart icon', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText(/HP/)).toBeInTheDocument();
        });
    });

    describe('daily breakdown', () => {
        it('renders adventure log with daily breakdown', () => {
            render(<AdventureResult />, { wrapper });

            expect(screen.getByText('Adventure Log')).toBeInTheDocument();
            expect(screen.getAllByText(/DAY \d/).length).toBeGreaterThan(0); // 3 days
            expect(screen.getByText('70 DMG')).toBeInTheDocument(); // First day damage
            expect(screen.getAllByText(/3 TASKS/).length).toBeGreaterThan(0);
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
            // Monster name includes "Unknown Monster" in component
            expect(screen.getByText(/Unknown/)).toBeInTheDocument();
            expect(screen.getByText('EASY')).toBeInTheDocument(); // Default tier
        });
    });

    describe('styling', () => {
        it('applies Design 1 classes', () => {
            const { container } = render(<AdventureResult />, { wrapper });

            // Check for border-4 class
            const borderedElements = container.querySelectorAll('.border-4');
            expect(borderedElements.length).toBeGreaterThan(0);

            // Check for shadow classes using class attribute matching
            const allElements = container.querySelectorAll('*');
            const hasShadow = Array.from(allElements).some(el =>
                el.className.toString().includes('shadow-')
            );
            expect(hasShadow).toBe(true);
        });
    });
});
