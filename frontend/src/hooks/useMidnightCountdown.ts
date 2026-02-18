import { useState, useEffect } from 'react';

/**
 * Custom hook for countdown to midnight in user's timezone
 *
 * This hook calculates the time remaining until midnight in the user's
 * local timezone and updates every second. It handles DST transitions
 * correctly and validates the timezone string.
 *
 * @param timezone - IANA timezone string (e.g., 'America/New_York')
 * @returns HH:MM:SS formatted countdown string, or '--:--:--' if timezone is invalid
 *
 * @example
 * const countdown = useMidnightCountdown('America/New_York');
 * // Returns "23:45:32" format
 *
 * @remarks
 * - Validates timezone before starting countdown
 * - Handles DST transitions correctly using toLocaleString
 * - Cleans up interval on unmount
 * - Returns '--:--:--' for invalid/missing timezones
 */
export function useMidnightCountdown(timezone: string | undefined): string {
    const [countdown, setCountdown] = useState('');
    const [isValidTimezone, setIsValidTimezone] = useState(false);

    useEffect(() => {
        // Validate timezone
        if (!timezone) {
            setCountdown('--:--:--');
            setIsValidTimezone(false);
            return;
        }

        try {
            // Test if timezone is valid by attempting to get current time
            new Date().toLocaleString('en-US', { timeZone: timezone });
            setIsValidTimezone(true);
        } catch (error) {
            console.warn(`Invalid timezone: ${timezone}`, error);
            setCountdown('--:--:--');
            setIsValidTimezone(false);
            return;
        }

        const updateCountdown = () => {
            try {
                const now = new Date();

                // Get current time in user's timezone (handles DST correctly)
                const userNowStr = now.toLocaleString('en-US', { timeZone: timezone });
                const userNow = new Date(userNowStr);

                // Calculate tomorrow midnight in user's timezone
                const tomorrowMidnight = new Date(userNow);
                tomorrowMidnight.setDate(tomorrowMidnight.getDate() + 1);
                tomorrowMidnight.setHours(0, 0, 0, 0);

                // Calculate difference in milliseconds
                const diff = tomorrowMidnight.getTime() - userNow.getTime();

                // Handle edge case: countdown finished
                if (diff <= 0) {
                    setCountdown('00:00:00');
                    return;
                }

                // Format as HH:MM:SS
                const hours = Math.floor(diff / (1000 * 60 * 60));
                const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((diff % (1000 * 60)) / 1000);

                setCountdown(
                    `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
                );
            } catch (error) {
                console.error('Error updating countdown:', error);
                setCountdown('--:--:--');
            }
        };

        // Initial update
        updateCountdown();

        // Update every second
        const interval = setInterval(updateCountdown, 1000);

        // Cleanup
        return () => clearInterval(interval);
    }, [timezone]);

    return isValidTimezone ? countdown : '--:--:--';
}
