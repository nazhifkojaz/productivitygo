import { describe, it, expect } from 'vitest';
import { formatNumber, formatTierEmoji, TIER_EMOJIS, type AdventureTier } from '../formatters';

describe('formatNumber', () => {
    describe('basic formatting', () => {
        it('returns "0" for zero', () => {
            expect(formatNumber(0)).toBe('0');
        });

        it('returns numbers below 1000 as-is', () => {
            expect(formatNumber(999)).toBe('999');
            expect(formatNumber(1)).toBe('1');
            expect(formatNumber(100)).toBe('100');
        });

        it('formats thousands with K suffix', () => {
            expect(formatNumber(1000)).toBe('1.0K');
            expect(formatNumber(1500)).toBe('1.5K');
            expect(formatNumber(9999)).toBe('10.0K');
            expect(formatNumber(123456)).toBe('123.5K');
        });

        it('formats millions with M suffix', () => {
            expect(formatNumber(1000000)).toBe('1.0M');
            expect(formatNumber(1500000)).toBe('1.5M');
            expect(formatNumber(9999999)).toBe('10.0M');
            expect(formatNumber(123456789)).toBe('123.5M');
        });
    });

    describe('edge cases', () => {
        it('handles undefined as "0"', () => {
            expect(formatNumber(undefined)).toBe('0');
        });

        it('handles null as "0"', () => {
            expect(formatNumber(null)).toBe('0');
        });

        it('handles NaN as "0"', () => {
            expect(formatNumber(NaN)).toBe('0');
        });

        it('handles Infinity as "∞"', () => {
            expect(formatNumber(Infinity)).toBe('∞');
            expect(formatNumber(-Infinity)).toBe('-∞');
        });

        it('handles negative numbers', () => {
            expect(formatNumber(-500)).toBe('-500');
            expect(formatNumber(-1500)).toBe('-1.5K');
            expect(formatNumber(-1500000)).toBe('-1.5M');
        });
    });

    describe('formatting consistency', () => {
        it('preserves decimal places for all values', () => {
            expect(formatNumber(1500)).toBe('1.5K');
            expect(formatNumber(1550)).toBe('1.6K');
            expect(formatNumber(1500000)).toBe('1.5M');
        });

        it('rounds correctly at boundaries', () => {
            expect(formatNumber(999)).toBe('999');
            expect(formatNumber(1000)).toBe('1.0K');
            expect(formatNumber(999499)).toBe('999.5K');
            expect(formatNumber(999999)).toBe('1000.0K');
        });
    });

    describe('large numbers', () => {
        it('handles billions', () => {
            expect(formatNumber(1500000000)).toBe('1500.0M');
            expect(formatNumber(1000000000)).toBe('1000.0M');
        });

        it('handles very large numbers', () => {
            expect(formatNumber(999999999999)).toBe('1000000.0M');
        });
    });
});

describe('formatTierEmoji', () => {
    describe('valid tiers', () => {
        it('returns correct emoji for easy tier', () => {
            expect(formatTierEmoji('easy')).toBe('🟢');
        });

        it('returns correct emoji for medium tier', () => {
            expect(formatTierEmoji('medium')).toBe('🟡');
        });

        it('returns correct emoji for hard tier', () => {
            expect(formatTierEmoji('hard')).toBe('🟠');
        });

        it('returns correct emoji for expert tier', () => {
            expect(formatTierEmoji('expert')).toBe('🔴');
        });

        it('returns correct emoji for boss tier', () => {
            expect(formatTierEmoji('boss')).toBe('👑');
        });
    });

    describe('case insensitivity', () => {
        it('handles uppercase tier names', () => {
            expect(formatTierEmoji('EASY')).toBe('🟢');
            expect(formatTierEmoji('HARD')).toBe('🟠');
            expect(formatTierEmoji('BOSS')).toBe('👑');
        });

        it('handles mixed case tier names', () => {
            expect(formatTierEmoji('Easy')).toBe('🟢');
            expect(formatTierEmoji('HaRd')).toBe('🟠');
            expect(formatTierEmoji('BoSs')).toBe('👑');
        });
    });

    describe('edge cases', () => {
        it('returns default emoji for undefined tier', () => {
            expect(formatTierEmoji(undefined)).toBe('🟢');
        });

        it('returns default emoji for invalid tier', () => {
            expect(formatTierEmoji('invalid')).toBe('🟢');
            expect(formatTierEmoji('')).toBe('🟢');
            expect(formatTierEmoji('EXTREME')).toBe('🟢');
        });

        it('accepts custom default tier', () => {
            expect(formatTierEmoji(undefined, 'boss')).toBe('👑');
            expect(formatTierEmoji('invalid', 'hard')).toBe('🟠');
        });
    });
});

describe('TIER_EMOJIS', () => {
    it('exports emoji mapping constant', () => {
        expect(TIER_EMOJIS).toEqual({
            easy: '🟢',
            medium: '🟡',
            hard: '🟠',
            expert: '🔴',
            boss: '👑',
        });
    });

    it('is typed correctly', () => {
        const tier: AdventureTier = 'hard';
        const emoji = TIER_EMOJIS[tier];
        expect(emoji).toBe('🟠');
    });
});
