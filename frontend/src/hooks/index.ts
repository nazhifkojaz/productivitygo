/**
 * Barrel export for all hooks
 *
 * This provides a cleaner import syntax:
 * import { useProfile, useBattleDetails } from '../hooks';
 */

// Profile hooks
export { useProfile } from './useProfile';
export { useProfileForm } from './useProfileForm';
export { usePublicProfile } from './usePublicProfile';

// Battle hooks
export { useCurrentBattle } from './useCurrentBattle';
export { useBattleDetails } from './useBattleDetails';
export { useBattleInvites } from './useBattleInvites';
export { useBattleMutations } from './useBattleMutations';
export { usePendingRematch } from './usePendingRematch';

// Adventure hooks
export { useCurrentAdventure } from './useCurrentAdventure';
export { useAdventureDetails } from './useAdventureDetails';
export { useAdventureMutations } from './useAdventureMutations';
export { useMonsters } from './useMonsters';

// Social hooks
export { useFollowers } from './useFollowers';
export { useFollowing } from './useFollowing';
export { useUserSearch } from './useUserSearch';
export { useSocialMutations } from './useSocialMutations';
