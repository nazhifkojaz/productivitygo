import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UserListItem from '../UserListItem';
import type { SocialUser } from '../../types/profile';

describe('UserListItem', () => {
    const mockUser: SocialUser = {
        id: 'user-1',
        username: 'RivalPlayer',
        avatar_emoji: '🔥',
        level: 7,
        rank: 'GOLD',
    };

    const defaultProps = {
        user: mockUser,
        onProfile: vi.fn(),
        isFollowing: false,
        onFollowToggle: vi.fn().mockResolvedValue(undefined),
    };

    describe('rendering', () => {
        it('renders username', () => {
            render(<UserListItem {...defaultProps} />);
            expect(screen.getByText('RivalPlayer')).toBeInTheDocument();
        });

        it('renders avatar emoji', () => {
            render(<UserListItem {...defaultProps} />);
            expect(screen.getByText('🔥')).toBeInTheDocument();
        });

        it('shows FOLLOW button when not following', () => {
            render(<UserListItem {...defaultProps} isFollowing={false} />);
            expect(screen.getByText('FOLLOW')).toBeInTheDocument();
        });

        it('shows UNFOLLOW button when following', () => {
            render(<UserListItem {...defaultProps} isFollowing={true} />);
            expect(screen.getByText('UNFOLLOW')).toBeInTheDocument();
        });
    });

    describe('interactions', () => {
        it('calls onProfile when user info clicked', async () => {
            const onProfile = vi.fn();
            const user = userEvent.setup();
            render(<UserListItem {...defaultProps} onProfile={onProfile} />);

            await user.click(screen.getByText('RivalPlayer'));
            expect(onProfile).toHaveBeenCalledTimes(1);
        });

        it('calls onFollowToggle when follow button clicked', async () => {
            const onFollowToggle = vi.fn().mockResolvedValue(undefined);
            const user = userEvent.setup();
            render(<UserListItem {...defaultProps} onFollowToggle={onFollowToggle} />);

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
            render(<UserListItem {...defaultProps} onFollowToggle={onFollowToggle} />);

            await user.click(screen.getByText('FOLLOW'));
            expect(screen.getByText('...')).toBeInTheDocument();

            resolveToggle!();
        });

        it('does not trigger onProfile when follow button clicked', async () => {
            const onProfile = vi.fn();
            const user = userEvent.setup();
            render(<UserListItem {...defaultProps} onProfile={onProfile} />);

            await user.click(screen.getByText('FOLLOW'));
            expect(onProfile).not.toHaveBeenCalled();
        });
    });

    describe('defaults', () => {
        it('uses default emoji when avatar_emoji is undefined', () => {
            const userWithoutEmoji: SocialUser = { id: 'u1', username: 'NoEmoji' };
            render(<UserListItem {...defaultProps} user={userWithoutEmoji} />);
            expect(screen.getByText('😀')).toBeInTheDocument();
        });
    });
});
