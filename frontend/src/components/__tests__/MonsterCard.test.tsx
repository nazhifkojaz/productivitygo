import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MonsterCard from '../MonsterCard';
import { Adventure } from '../../hooks/useCurrentAdventure';

describe('MonsterCard', () => {
    const mockAdventure: Adventure = {
        id: 'adv-123',
        user_id: 'user-123',
        monster_id: 'monster-123',
        duration: 5,
        start_date: '2026-02-01',
        deadline: '2026-02-05',
        monster_max_hp: 200,
        monster_current_hp: 150,
        status: 'active',
        current_round: 2,
        total_damage_dealt: 50,
        xp_earned: 0,
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
        app_state: 'ACTIVE',
        days_remaining: 3,
    };

    describe('rendering', () => {
        it('renders monster information', () => {
            render(<MonsterCard adventure={mockAdventure} />);

            expect(screen.getByText('Procrastination Goblin')).toBeInTheDocument();
            expect(screen.getByText('👺')).toBeInTheDocument();
            // MEDIUM TIER text is uppercase in component
            expect(screen.getByText(/MEDIUM/)).toBeInTheDocument();
        });

        it('renders HP bar with correct values', () => {
            render(<MonsterCard adventure={mockAdventure} />);

            // The HP display shows values separated by " / "
            expect(screen.getByText(/150/)).toBeInTheDocument();
            expect(screen.getByText(/200/)).toBeInTheDocument();
            expect(screen.getByText(/HP/)).toBeInTheDocument();
        });

        it('renders stats grid with correct values', () => {
            render(<MonsterCard adventure={mockAdventure} />);

            expect(screen.getByText('50')).toBeInTheDocument(); // Damage
            expect(screen.getByText('3d')).toBeInTheDocument(); // Days remaining
            expect(screen.getByText('2')).toBeInTheDocument(); // Breaks remaining (2 - 0 = 2)
        });

        it('renders monster description', () => {
            render(<MonsterCard adventure={mockAdventure} />);

            expect(screen.getByText(/"There's still time..."/)).toBeInTheDocument();
        });

        it('renders black header bar with // MONSTER //', () => {
            render(<MonsterCard adventure={mockAdventure} />);

            expect(screen.getByText('// MONSTER //')).toBeInTheDocument();
        });
    });

    describe('HP bar calculation', () => {
        it('calculates HP percentage correctly for 150/200', () => {
            const { container } = render(<MonsterCard adventure={mockAdventure} />);

            const hpBar = container.querySelector('.h-full.bg-gradient-to-r');
            expect(hpBar).toHaveStyle({ width: '75%' }); // 150/200 = 75%
        });

        it('calculates HP percentage correctly for critical health', () => {
            const lowHpAdventure = { ...mockAdventure, monster_current_hp: 40, monster_max_hp: 200 };
            const { container } = render(<MonsterCard adventure={lowHpAdventure} />);

            const hpBar = container.querySelector('.h-full.bg-gradient-to-r');
            expect(hpBar).toHaveStyle({ width: '20%' }); // 40/200 = 20%
        });

        it('calculates HP percentage correctly for full health', () => {
            const fullHpAdventure = { ...mockAdventure, monster_current_hp: 200, monster_max_hp: 200 };
            const { container } = render(<MonsterCard adventure={fullHpAdventure} />);

            const hpBar = container.querySelector('.h-full.bg-gradient-to-r');
            expect(hpBar).toHaveStyle({ width: '100%' });
        });
    });

    describe('break days calculation', () => {
        it('shows remaining breaks correctly', () => {
            const adventureWithBreaks = { ...mockAdventure, break_days_used: 1, max_break_days: 2 };
            render(<MonsterCard adventure={adventureWithBreaks} />);

            expect(screen.getByText('1')).toBeInTheDocument(); // 2 - 1 = 1
        });

        it('shows zero when all breaks used', () => {
            const noBreaksAdventure = { ...mockAdventure, break_days_used: 2, max_break_days: 2 };
            render(<MonsterCard adventure={noBreaksAdventure} />);

            expect(screen.getByText('0')).toBeInTheDocument(); // 2 - 2 = 0
        });
    });

    describe('on-break state', () => {
        it('shows break banner when on break', () => {
            const onBreakAdventure = { ...mockAdventure, is_on_break: true };
            render(<MonsterCard adventure={onBreakAdventure} />);

            expect(screen.getByText('REST DAY - Adventure paused')).toBeInTheDocument();
        });

        it('does not show break banner when not on break', () => {
            render(<MonsterCard adventure={mockAdventure} />);

            expect(screen.queryByText('REST DAY - Adventure paused')).not.toBeInTheDocument();
        });
    });

    describe('tier colors', () => {
        it('shows correct color for easy tier', () => {
            const easyAdventure = {
                ...mockAdventure,
                monster: { ...mockAdventure.monster!, tier: 'easy' as const },
            };
            const { container } = render(<MonsterCard adventure={easyAdventure} />);

            const tierBadge = container.querySelector('.bg-\\[\\#2A9D8F\\]');
            expect(tierBadge).toBeInTheDocument();
        });

        it('shows correct color for medium tier', () => {
            const { container } = render(<MonsterCard adventure={mockAdventure} />);

            const tierBadge = container.querySelector('.bg-\\[\\#F4A261\\]');
            expect(tierBadge).toBeInTheDocument();
        });

        it('shows correct color for hard tier', () => {
            const hardAdventure = {
                ...mockAdventure,
                monster: { ...mockAdventure.monster!, tier: 'hard' as const },
            };
            const { container } = render(<MonsterCard adventure={hardAdventure} />);

            const tierBadge = container.querySelector('.bg-\\[\\#E63946\\]');
            expect(tierBadge).toBeInTheDocument();
        });

        it('shows correct color for expert tier', () => {
            const expertAdventure = {
                ...mockAdventure,
                monster: { ...mockAdventure.monster!, tier: 'expert' as const },
            };
            const { container } = render(<MonsterCard adventure={expertAdventure} />);

            const tierBadge = container.querySelector('.bg-\\[\\#9D4EDD\\]');
            expect(tierBadge).toBeInTheDocument();
        });

        it('shows correct color for boss tier', () => {
            const bossAdventure = {
                ...mockAdventure,
                monster: { ...mockAdventure.monster!, tier: 'boss' as const },
            };
            const { container } = render(<MonsterCard adventure={bossAdventure} />);

            const tierBadge = container.querySelector('.bg-black');
            expect(tierBadge).toBeInTheDocument();
        });
    });

    describe('fallback values', () => {
        it('shows default monster emoji when monster is missing', () => {
            const noMonsterAdventure = { ...mockAdventure, monster: undefined };
            render(<MonsterCard adventure={noMonsterAdventure} />);

            expect(screen.getByText('👹')).toBeInTheDocument(); // Default emoji
        });

        it('shows Unknown Monster name when monster is missing', () => {
            const noMonsterAdventure = { ...mockAdventure, monster: undefined };
            render(<MonsterCard adventure={noMonsterAdventure} />);

            expect(screen.getByText('Unknown Monster')).toBeInTheDocument();
        });

        it('shows 0 days when days_remaining is undefined', () => {
            const noDaysAdventure = { ...mockAdventure, days_remaining: undefined };
            render(<MonsterCard adventure={noDaysAdventure} />);

            expect(screen.getByText('0d')).toBeInTheDocument();
        });
    });

    describe('styling', () => {
        it('applies Design 1 classes', () => {
            const { container } = render(<MonsterCard adventure={mockAdventure} />);

            const card = container.querySelector('aside');
            expect(card).toHaveClass('border-4');
            // Check for shadow in class
            expect(card?.className).toContain('shadow-');
        });
    });
});
