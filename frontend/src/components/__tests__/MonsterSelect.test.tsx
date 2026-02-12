import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MonsterSelect from '../MonsterSelect';
import { Monster } from '../../hooks/useMonsters';

describe('MonsterSelect', () => {
    const mockMonsters: Monster[] = [
        {
            id: 'monster-1',
            name: 'Lazy Slime',
            emoji: '🟢',
            tier: 'easy',
            base_hp: 100,
            description: 'Just five more minutes...',
            monster_type: 'sloth',
        },
        {
            id: 'monster-2',
            name: 'Procrastination Goblin',
            emoji: '👺',
            tier: 'medium',
            base_hp: 200,
            description: "There's still time...",
            monster_type: 'sloth',
        },
        {
            id: 'monster-3',
            name: 'Burnout Specter',
            emoji: '👻',
            tier: 'hard',
            base_hp: 320,
            description: 'Drains energy you did not know you had',
            monster_type: 'burnout',
        },
        {
            id: 'monster-4',
            name: 'Anxiety Dragon',
            emoji: '🐲',
            tier: 'expert',
            base_hp: 450,
            description: 'What if everything goes wrong?',
            monster_type: 'titan',
        },
    ];

    const defaultProps = {
        monsters: mockMonsters,
        refreshesRemaining: 3,
        onSelect: vi.fn(),
        onRefresh: vi.fn(),
        isLoading: false,
        isRefreshing: false,
    };

    const getMonsterCards = (container: HTMLElement) => {
        return container.querySelectorAll('button.p-4'); // Monster cards have p-4 class
    };

    describe('rendering', () => {
        it('renders header with title', () => {
            render(<MonsterSelect {...defaultProps} />);

            expect(screen.getByText('Choose Your Challenge')).toBeInTheDocument();
        });

        it('renders refresh button with remaining count', () => {
            render(<MonsterSelect {...defaultProps} />);

            expect(screen.getByText(/Refresh \(3\)/)).toBeInTheDocument();
        });

        it('renders all 4 monsters in grid', () => {
            render(<MonsterSelect {...defaultProps} />);

            expect(screen.getByText('Lazy Slime')).toBeInTheDocument();
            expect(screen.getByText('Procrastination Goblin')).toBeInTheDocument();
            expect(screen.getByText('Burnout Specter')).toBeInTheDocument();
            expect(screen.getByText('Anxiety Dragon')).toBeInTheDocument();
        });

        it('renders monster emojis', () => {
            render(<MonsterSelect {...defaultProps} />);

            expect(screen.getByText('🟢')).toBeInTheDocument();
            expect(screen.getByText('👺')).toBeInTheDocument();
            expect(screen.getByText('👻')).toBeInTheDocument();
            expect(screen.getByText('🐲')).toBeInTheDocument();
        });

        it('renders monster HP values', () => {
            render(<MonsterSelect {...defaultProps} />);

            expect(screen.getByText('HP: 100')).toBeInTheDocument();
            expect(screen.getByText('HP: 200')).toBeInTheDocument();
            expect(screen.getByText('HP: 320')).toBeInTheDocument();
            expect(screen.getByText('HP: 450')).toBeInTheDocument();
        });

        it('renders monster descriptions', () => {
            render(<MonsterSelect {...defaultProps} />);

            expect(screen.getByText(/Just five more minutes\.\.\./)).toBeInTheDocument();
            expect(screen.getByText(/There's still time\.\.\./)).toBeInTheDocument();
        });

        it('renders tier badges (lowercase with uppercase CSS)', () => {
            render(<MonsterSelect {...defaultProps} />);

            // Component renders lowercase tier, CSS makes it uppercase
            expect(screen.getByText('easy')).toBeInTheDocument();
            expect(screen.getByText('medium')).toBeInTheDocument();
            expect(screen.getByText('hard')).toBeInTheDocument();
            expect(screen.getByText('expert')).toBeInTheDocument();
        });
    });

    describe('monster selection', () => {
        it('calls onSelect when monster card is clicked', async () => {
            const user = userEvent.setup();
            const onSelect = vi.fn();

            render(<MonsterSelect {...defaultProps} onSelect={onSelect} />);

            const firstMonster = screen.getByText('Lazy Slime').closest('button');
            await user.click(firstMonster!);

            expect(onSelect).toHaveBeenCalledWith('monster-1');
        });

        it('calls onSelect with correct monster ID for each card', async () => {
            const user = userEvent.setup();
            const onSelect = vi.fn();

            const { container } = render(<MonsterSelect {...defaultProps} onSelect={onSelect} />);

            const cards = getMonsterCards(container);
            await user.click(cards[1]); // Second monster

            expect(onSelect).toHaveBeenCalledWith('monster-2');
        });
    });

    describe('refresh functionality', () => {
        it('calls onRefresh when refresh button is clicked', async () => {
            const user = userEvent.setup();
            const onRefresh = vi.fn();

            render(<MonsterSelect {...defaultProps} onRefresh={onRefresh} />);

            const refreshButton = screen.getByText(/Refresh \(3\)/);
            await user.click(refreshButton);

            expect(onRefresh).toHaveBeenCalledTimes(1);
        });

        it('disables refresh button when no refreshes remaining', () => {
            render(<MonsterSelect {...defaultProps} refreshesRemaining={0} />);

            const refreshButton = screen.getByText(/Refresh \(0\)/);
            expect(refreshButton).toBeDisabled();
        });

        it('shows correct remaining count', () => {
            const { rerender } = render(<MonsterSelect {...defaultProps} refreshesRemaining={2} />);
            expect(screen.getByText(/Refresh \(2\)/)).toBeInTheDocument();

            rerender(<MonsterSelect {...defaultProps} refreshesRemaining={1} />);
            expect(screen.getByText(/Refresh \(1\)/)).toBeInTheDocument();
        });
    });

    describe('loading states', () => {
        it('shows loading overlay when isLoading is true', () => {
            render(<MonsterSelect {...defaultProps} isLoading={true} />);

            expect(screen.getByText('Starting adventure...')).toBeInTheDocument();
        });

        it('shows loader when isRefreshing is true', () => {
            render(<MonsterSelect {...defaultProps} isRefreshing={true} />);

            // Should show animated loader icon
            const refreshButton = screen.getByText(/Refresh/);
            expect(refreshButton.querySelector('.animate-spin')).toBeInTheDocument();
        });

        it('does not show loading overlay when not loading', () => {
            render(<MonsterSelect {...defaultProps} />);

            expect(screen.queryByText('Starting adventure...')).not.toBeInTheDocument();
        });
    });

    describe('disabled states', () => {
        it('disables monster cards when isLoading is true', () => {
            const { container } = render(<MonsterSelect {...defaultProps} isLoading={true} />);

            const cards = getMonsterCards(container);
            cards.forEach(card => {
                expect(card).toBeDisabled();
            });
        });

        it('disables refresh button when isRefreshing is true', () => {
            render(<MonsterSelect {...defaultProps} isRefreshing={true} refreshesRemaining={3} />);

            const refreshButton = screen.getByText(/Refresh/);
            expect(refreshButton).toBeDisabled();
        });
    });

    describe('tier styling', () => {
        it('applies correct tier classes for easy tier', () => {
            render(<MonsterSelect {...defaultProps} />);

            const easyCard = screen.getByText('Lazy Slime').closest('button');
            expect(easyCard).toHaveClass('bg-green-100', 'border-green-500');
        });

        it('applies correct tier classes for medium tier', () => {
            render(<MonsterSelect {...defaultProps} />);

            const mediumCard = screen.getByText('Procrastination Goblin').closest('button');
            expect(mediumCard).toHaveClass('bg-yellow-100', 'border-yellow-500');
        });

        it('applies correct tier classes for hard tier', () => {
            render(<MonsterSelect {...defaultProps} />);

            const hardCard = screen.getByText('Burnout Specter').closest('button');
            expect(hardCard).toHaveClass('bg-orange-100', 'border-orange-500');
        });

        it('applies correct tier classes for expert tier', () => {
            render(<MonsterSelect {...defaultProps} />);

            const expertCard = screen.getByText('Anxiety Dragon').closest('button');
            expect(expertCard).toHaveClass('bg-red-100', 'border-red-500');
        });
    });

    describe('monster type labels', () => {
        it('renders monster type label on each card', () => {
            render(<MonsterSelect {...defaultProps} />);

            const slothLabels = screen.getAllByText('🦥 Sloth');
            expect(slothLabels).toHaveLength(2); // Both sloth monsters
            expect(screen.getByText('🔥 Burnout')).toBeInTheDocument();
            expect(screen.getByText('🗿 Titan')).toBeInTheDocument();
        });

        it('does not render type label when monster_type is missing', () => {
            const monstersWithoutType = mockMonsters.map(m => ({
                ...m,
                monster_type: undefined as any
            }));
            render(<MonsterSelect {...defaultProps} monsters={monstersWithoutType} />);

            expect(screen.queryByText('🦥 Sloth')).not.toBeInTheDocument();
        });
    });

    describe('grid layout', () => {
        it('renders monsters in 2x2 grid', () => {
            const { container } = render(<MonsterSelect {...defaultProps} />);

            const grid = container.querySelector('.grid');
            expect(grid).toHaveClass('grid-cols-2');
        });
    });

    describe('styling', () => {
        it('applies neo-brutalist classes to cards', () => {
            const { container } = render(<MonsterSelect {...defaultProps} />);

            const cards = getMonsterCards(container);
            cards.forEach(card => {
                expect(card).toHaveClass('border-3', 'shadow-neo');
            });
        });
    });
});
