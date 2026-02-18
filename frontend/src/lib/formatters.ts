/**
 * Formatters for displaying data in the UI
 *
 * This module contains reusable formatting utilities for numbers,
 * dates, and game-specific data like adventure tiers.
 */

/**
 * Format large numbers with K/M suffixes
 * @param num - The number to format (undefined/null treated as 0)
 * @returns Formatted string (e.g., "1.5K", "2.3M", "999")
 *
 * @example
 * formatNumber(1500)      // "1.5K"
 * formatNumber(1500000)   // "1.5M"
 * formatNumber(999)       // "999"
 * formatNumber(0)         // "0"
 * formatNumber(NaN)       // "0"
 * formatNumber(Infinity)  // "∞"
 * formatNumber(-Infinity) // "-∞"
 */
export function formatNumber(num: number | undefined | null): string {
    // Handle null/undefined
    if (num === undefined || num === null) {
        return '0';
    }

    // Handle infinite numbers (must check before checking num === 0)
    if (!Number.isFinite(num)) {
        if (Number.isNaN(num)) return '0';
        // Handle both positive and negative infinity
        return num < 0 ? '-∞' : '∞';
    }

    // Handle zero
    if (num === 0) {
        return '0';
    }

    // Handle negative numbers (absolute value for formatting, restore sign)
    const isNegative = num < 0;
    const absNum = Math.abs(num);

    // Format based on magnitude - keep .0 for exact thousands/millions (original behavior)
    let formatted: string;
    if (absNum >= 1000000) {
        formatted = `${(absNum / 1000000).toFixed(1)}M`;
    } else if (absNum >= 1000) {
        formatted = `${(absNum / 1000).toFixed(1)}K`;
    } else {
        formatted = absNum.toString();
    }

    return isNegative ? `-${formatted}` : formatted;
}

/**
 * Adventure tier levels
 */
export type AdventureTier = 'easy' | 'medium' | 'hard' | 'expert' | 'boss';

/**
 * Emoji mapping for adventure tiers
 */
const TIER_EMOJIS: Record<AdventureTier, string> = {
    easy: '🟢',
    medium: '🟡',
    hard: '🟠',
    expert: '🔴',
    boss: '👑',
} as const;

/**
 * Format tier as emoji with fallback
 * @param tier - The tier string (case-insensitive)
 * @param defaultTier - Fallback tier if input is invalid (default: 'easy')
 * @returns Emoji character
 *
 * @example
 * formatTierEmoji('hard')        // '🟠'
 * formatTierEmoji('HARD')        // '🟠'
 * formatTierEmoji('invalid')     // '🟢' (default)
 * formatTierEmoji(undefined)     // '🟢' (default)
 */
export function formatTierEmoji(tier?: string, defaultTier: AdventureTier = 'easy'): string {
    if (!tier) {
        return TIER_EMOJIS[defaultTier];
    }

    const normalizedTier = tier.toLowerCase() as AdventureTier;
    return TIER_EMOJIS[normalizedTier] || TIER_EMOJIS[defaultTier];
}

/**
 * Get tier emoji directly (shorthand for formatTierEmoji)
 */
export { TIER_EMOJIS };
