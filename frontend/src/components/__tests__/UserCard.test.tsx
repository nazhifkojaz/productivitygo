import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UserCard from '../UserCard';
import type { SocialUser } from '../../types/profile';

describe('UserCard', () => {
    const mockUser: SocialUser = {
        id: 'user-1',
        username: 'TestUser',
        avatar_emoji: '🎮',
        level: 3,
        rank: 'SILVER',
    };

    const defaultProps = {
        user: mockUser,
        onViewProfile: vi.fn(),
    };

    describe('rendering', () => {
        it('renders username', () => {
            render(<UserCard {...defaultProps} />);
            expect(screen.getByText('TestUser')).toBeInTheDocument();
        });

        it('renders avatar emoji', () => {
            render(<UserCard {...defaultProps} />);
            expect(screen.getByText('🎮')).toBeInTheDocument();
        });

        it('renders level and rank', () => {
            render(<UserCard {...defaultProps} />);
            expect(screen.getByText('LVL 3 · SILVER')).toBeInTheDocument();
        });

        it('shows VIEW button when no follow toggle provided', () => {
            render(<UserCard {...defaultProps} />);
            expect(screen.getByText('VIEW')).toBeInTheDocument();
        });

        it('shows FOLLOW button when follow toggle provided and not following', () => {
            render(
                <UserCard
                    {...defaultProps}
                    isFollowing={false}
                    onFollowToggle={vi.fn().mockResolvedValue(undefined)}
                />
            );
            expect(screen.getByText('FOLLOW')).toBeInTheDocument();
        });

        it('shows UNFOLLOW button when following', () => {
            render(
                <UserCard
                    {...defaultProps}
                    isFollowing={true}
                    onFollowToggle={vi.fn().mockResolvedValue(undefined)}
                />
            );
            expect(screen.getByText('UNFOLLOW')).toBeInTheDocument();
        });
    });

    describe('interactions', () => {
        it('calls onViewProfile when card clicked', async () => {
            const onViewProfile = vi.fn();
            const user = userEvent.setup();
            render(<UserCard {...defaultProps} onViewProfile={onViewProfile} />);

            await user.click(screen.getByText('TestUser'));
            expect(onViewProfile).toHaveBeenCalledTimes(1);
        });

        it('calls onFollowToggle when follow button clicked', async () => {
            const onFollowToggle = vi.fn().mockResolvedValue(undefined);
            const user = userEvent.setup();
            render(
                <UserCard
                    {...defaultProps}
                    isFollowing={false}
                    onFollowToggle={onFollowToggle}
                />
            );

            await user.click(screen.getByText('FOLLOW'));
            await waitFor(() => {
                expect(onFollowToggle).toHaveBeenCalledTimes(1);
            });
        });

        it('shows loading state during follow toggle', async () => {
            let resolveToggle: () => void;
            const onFollowToggle = vi.fn(
                () => new Promise<void>((resolve) => { resolveToggle = resolve; })
            );
            const user = userEvent.setup();
            render(
                <UserCard
                    {...defaultProps}
                    isFollowing={false}
                    onFollowToggle={onFollowToggle}
                />
            );

            await user.click(screen.getByText('FOLLOW'));
            expect(screen.getByText('...')).toBeInTheDocument();

            resolveToggle!();
        });
    });

    describe('defaults', () => {
        it('uses default emoji when avatar_emoji is undefined', () => {
            const userWithoutEmoji: SocialUser = { id: 'u1', username: 'NoEmoji' };
            render(<UserCard user={userWithoutEmoji} onViewProfile={vi.fn()} />);
            expect(screen.getByText('😀')).toBeInTheDocument();
        });

        it('defaults level to 1 when not provided', () => {
            const minimalUser: SocialUser = { id: 'u1', username: 'Min' };
            render(<UserCard user={minimalUser} onViewProfile={vi.fn()} />);
            expect(screen.getByText('LVL 1 · BRONZE')).toBeInTheDocument();
        });
    });
});
