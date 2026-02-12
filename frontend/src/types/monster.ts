import type { TaskCategory } from './task';

/**
 * Monster type - determines weaknesses and resistances
 */
export type MonsterType =
    | 'sloth'
    | 'chaos'
    | 'fog'
    | 'burnout'
    | 'stagnation'
    | 'shadow'
    | 'titan';

/**
 * Monster type metadata for UI display
 */
export const MONSTER_TYPES = [
    {
        key: 'sloth',
        label: 'Sloth',
        theme: 'Laziness',
        emoji: '🦥',
        description: 'Procrastination and avoidance',
    },
    {
        key: 'chaos',
        label: 'Chaos',
        theme: 'Disorder',
        emoji: '🌀',
        description: 'Disorganization and scattered focus',
    },
    {
        key: 'fog',
        label: 'Fog',
        theme: 'Distraction',
        emoji: '🌫️',
        description: 'Confusion and loss of clarity',
    },
    {
        key: 'burnout',
        label: 'Burnout',
        theme: 'Exhaustion',
        emoji: '🔥',
        description: 'Overwhelm and depletion',
    },
    {
        key: 'stagnation',
        label: 'Stagnation',
        theme: 'Boredom',
        emoji: '🪨',
        description: 'Routine fatigue and stuckness',
    },
    {
        key: 'shadow',
        label: 'Shadow',
        theme: 'Isolation',
        emoji: '👤',
        description: 'Negativity and self-doubt',
    },
    {
        key: 'titan',
        label: 'Titan',
        theme: 'Overwhelm',
        emoji: '🗿',
        description: 'Insurmountable challenges',
    },
] as const;

/**
 * Helper to get monster type metadata by key
 */
export const getMonsterTypeMeta = (type: MonsterType) =>
    MONSTER_TYPES.find((t) => t.key === type) ?? MONSTER_TYPES[0];

/**
 * Type discovery - what effectiveness a user has learned about a matchup
 *
 * Note: monster_type is optional because GET /adventures/current embeds
 * discoveries without monster_type (already filtered by current monster's type)
 */
export interface TypeDiscovery {
    monster_type?: MonsterType;
    task_category: TaskCategory;
    effectiveness: 'super_effective' | 'neutral' | 'resisted';
}

/**
 * Monster type definition
 */
export interface Monster {
    id: string;
    name: string;
    emoji: string;
    tier: 'easy' | 'medium' | 'hard' | 'expert' | 'boss';
    base_hp: number;
    description: string;
    monster_type: MonsterType;
}

/**
 * Response from /adventures/monsters endpoint
 */
export interface MonsterPoolResponse {
    monsters: Monster[];
    refreshes_remaining: number;
    unlocked_tiers: string[];
    current_rating: number;
}
