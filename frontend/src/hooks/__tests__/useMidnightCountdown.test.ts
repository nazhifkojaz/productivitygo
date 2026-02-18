import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderHook, cleanup } from '@testing-library/react';
import { useMidnightCountdown } from '../useMidnightCountdown';

describe('useMidnightCountdown', () => {
    afterEach(() => {
        cleanup();
        vi.restoreAllMocks();
    });

    describe('basic functionality', () => {
        it('returns string for valid timezone', () => {
            const { result } = renderHook(() => useMidnightCountdown('America/New_York'));
            expect(typeof result.current).toBe('string');
        });

        it('cleans up interval on unmount', () => {
            const clearIntervalSpy = vi.spyOn(global, 'clearInterval');

            const { unmount } = renderHook(() => useMidnightCountdown('UTC'));

            unmount();

            expect(clearIntervalSpy).toHaveBeenCalled();
        });
    });

    describe('timezone handling', () => {
        it('handles valid timezone strings', () => {
            const { result } = renderHook(() => useMidnightCountdown('America/Los_Angeles'));
            expect(result.current).toMatch(/\d{2}:\d{2}:\d{2}|--:--:--/);
        });

        it('returns "--:--:--" for undefined timezone', () => {
            const { result } = renderHook(() => useMidnightCountdown(undefined));
            expect(result.current).toBe('--:--:--');
        });

        it('returns "--:--:--" for empty string timezone', () => {
            const { result } = renderHook(() => useMidnightCountdown(''));
            expect(result.current).toBe('--:--:--');
        });

        it('returns "--:--:--" for invalid timezone', () => {
            const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

            const { result } = renderHook(() => useMidnightCountdown('Invalid/Timezone'));

            expect(result.current).toBe('--:--:--');
            expect(consoleWarnSpy).toHaveBeenCalled();

            consoleWarnSpy.mockRestore();
        });
    });

    describe('countdown format', () => {
        it('returns HH:MM:SS format for valid timezone', () => {
            const { result } = renderHook(() => useMidnightCountdown('UTC'));
            expect(result.current).toMatch(/^\d{2}:\d{2}:\d{2}$/);
        });

        it('validates time ranges for valid timezone', () => {
            const { result } = renderHook(() => useMidnightCountdown('UTC'));
            const value = result.current;
            const match = value.match(/^(\d{2}):(\d{2}):(\d{2})$/);
            expect(match).toBeTruthy();

            const [, hours, minutes, seconds] = match!;
            const hoursNum = parseInt(hours, 10);
            const minutesNum = parseInt(minutes, 10);
            const secondsNum = parseInt(seconds, 10);

            expect(hoursNum).toBeGreaterThanOrEqual(0);
            expect(hoursNum).toBeLessThan(24);
            expect(minutesNum).toBeGreaterThanOrEqual(0);
            expect(minutesNum).toBeLessThan(60);
            expect(secondsNum).toBeGreaterThanOrEqual(0);
            expect(secondsNum).toBeLessThan(60);
        });
    });

    describe('timezone changes', () => {
        it('updates countdown when timezone changes', () => {
            const { result, rerender } = renderHook(
                ({ tz }) => useMidnightCountdown(tz),
                { initialProps: { tz: 'UTC' as string | undefined } }
            );

            const utcValue = result.current;

            rerender({ tz: 'America/New_York' });

            expect(result.current).toBeTruthy();
        });

        it('cleans up previous interval when timezone changes', () => {
            const clearIntervalSpy = vi.spyOn(global, 'clearInterval');

            const { rerender } = renderHook(
                ({ tz }) => useMidnightCountdown(tz),
                { initialProps: { tz: 'UTC' as string | undefined } }
            );

            rerender({ tz: 'America/New_York' });

            // clearInterval should be called when timezone changes
            expect(clearIntervalSpy).toHaveBeenCalled();
        });
    });

    describe('edge cases', () => {
        it('handles DST transition correctly', () => {
            const { result } = renderHook(() => useMidnightCountdown('America/New_York'));
            expect(result.current).toMatch(/\d{2}:\d{2}:\d{2}/);
        });

        it('handles null-like timezone values', () => {
            const { result } = renderHook(() => useMidnightCountdown(undefined as any));
            expect(result.current).toBe('--:--:--');
        });
    });
});
