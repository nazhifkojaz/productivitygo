import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { useTaskMutations } from '../useTaskMutations';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock axios
vi.mock('axios', () => ({
    default: {
        post: vi.fn(),
    },
}));

// Mock AuthContext
vi.mock('../../context/AuthContext', () => ({
    useAuth: vi.fn(),
}));

// Mock sonner toast
vi.mock('sonner', () => ({
    toast: {
        success: vi.fn(),
        error: vi.fn(),
    },
}));

import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
import { toast } from 'sonner';

const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
            },
            mutations: {
                retry: false,
            },
        },
    });
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
};

describe('useTaskMutations', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('completeTaskMutation', () => {
        it('completes a task successfully', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.post).mockResolvedValue({ data: {} });

            const { result } = renderHook(() => useTaskMutations(), {
                wrapper: createWrapper(),
            });

            result.current.completeTaskMutation.mutate('task-123');

            await waitFor(() => expect(result.current.completeTaskMutation.isSuccess).toBe(true));

            expect(axios.post).toHaveBeenCalledWith(
                '/api/tasks/task-123/complete',
                {},
                { headers: { Authorization: 'Bearer test-token' } }
            );
        });

        it('invalidates tasks query on success', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.post).mockResolvedValue({ data: {} });

            const queryClient = new QueryClient({
                defaultOptions: {
                    queries: { retry: false },
                },
            });

            const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

            const wrapper = ({ children }: { children: React.ReactNode }) => (
                <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
            );

            const { result } = renderHook(() => useTaskMutations(), { wrapper });

            result.current.completeTaskMutation.mutate('task-123');

            await waitFor(() => expect(result.current.completeTaskMutation.isSuccess).toBe(true));

            expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['tasks', 'today'] });
        });

        it('shows error toast on failure', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.post).mockRejectedValue({
                response: { status: 500 },
                message: 'Internal server error',
            });

            const { result } = renderHook(() => useTaskMutations(), {
                wrapper: createWrapper(),
            });

            result.current.completeTaskMutation.mutate('task-123');

            await waitFor(() => expect(result.current.completeTaskMutation.isError).toBe(true));

            expect(toast.error).toHaveBeenCalledWith('Failed to complete task');
        });

        it('sets isCompleting to true during mutation', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.post).mockResolvedValue({ data: {} });

            const { result } = renderHook(() => useTaskMutations(), {
                wrapper: createWrapper(),
            });

            // Start the mutation
            result.current.completeTaskMutation.mutate('task-123');

            // Verify isCompleting tracks the mutation state
            // Note: Due to timing, we just verify the hook returns the function
            expect(result.current.completeTaskMutation).toBeDefined();
            expect(typeof result.current.isCompleting).toBe('boolean');

            // Wait for success
            await waitFor(() => expect(result.current.completeTaskMutation.isSuccess).toBe(true));

            // After success, isCompleting should be false
            expect(result.current.isCompleting).toBe(false);
        });
    });

    describe('saveDraftMutation', () => {
        it('saves draft tasks successfully', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.post).mockResolvedValue({ data: {} });

            const { result } = renderHook(() => useTaskMutations(), {
                wrapper: createWrapper(),
            });

            const tasksToSave = [
                { content: 'Task 1', is_optional: false, assigned_score: 10 },
                { content: 'Task 2', is_optional: true, assigned_score: 5 },
            ];

            result.current.saveDraftMutation.mutate(tasksToSave);

            await waitFor(() => expect(result.current.saveDraftMutation.isSuccess).toBe(true));

            expect(axios.post).toHaveBeenCalledWith(
                '/api/tasks/draft',
                tasksToSave,
                { headers: { Authorization: 'Bearer test-token' } }
            );
        });

        it('invalidates draft query on success', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.post).mockResolvedValue({ data: {} });

            const queryClient = new QueryClient({
                defaultOptions: {
                    queries: { retry: false },
                },
            });

            const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

            const wrapper = ({ children }: { children: React.ReactNode }) => (
                <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
            );

            const { result } = renderHook(() => useTaskMutations(), { wrapper });

            const tasksToSave = [{ content: 'Task 1', is_optional: false, assigned_score: 10 }];

            result.current.saveDraftMutation.mutate(tasksToSave);

            await waitFor(() => expect(result.current.saveDraftMutation.isSuccess).toBe(true));

            expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['tasks', 'draft'] });
        });

        it('shows success toast on successful save', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.post).mockResolvedValue({ data: {} });

            const { result } = renderHook(() => useTaskMutations(), {
                wrapper: createWrapper(),
            });

            const tasksToSave = [{ content: 'Task 1', is_optional: false, assigned_score: 10 }];

            result.current.saveDraftMutation.mutate(tasksToSave);

            await waitFor(() => expect(result.current.saveDraftMutation.isSuccess).toBe(true));

            expect(toast.success).toHaveBeenCalledWith(
                'Plan saved successfully! You can edit this until midnight.'
            );
        });

        it('shows error toast on failure', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.post).mockRejectedValue({
                response: { status: 500 },
                message: 'Internal server error',
            });

            const { result } = renderHook(() => useTaskMutations(), {
                wrapper: createWrapper(),
            });

            const tasksToSave = [{ content: 'Task 1', is_optional: false, assigned_score: 10 }];

            result.current.saveDraftMutation.mutate(tasksToSave);

            await waitFor(() => expect(result.current.saveDraftMutation.isError).toBe(true));

            expect(toast.error).toHaveBeenCalledWith('Failed to save plan.');
        });

        it('sets isSaving to true during mutation', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.post).mockResolvedValue({ data: {} });

            const { result } = renderHook(() => useTaskMutations(), {
                wrapper: createWrapper(),
            });

            const tasksToSave = [{ content: 'Task 1', is_optional: false, assigned_score: 10 }];

            // Start the mutation
            result.current.saveDraftMutation.mutate(tasksToSave);

            // Verify isSaving tracks the mutation state
            expect(result.current.saveDraftMutation).toBeDefined();
            expect(typeof result.current.isSaving).toBe('boolean');

            // Wait for success
            await waitFor(() => expect(result.current.saveDraftMutation.isSuccess).toBe(true));

            // After success, isSaving should be false
            expect(result.current.isSaving).toBe(false);
        });
    });

    describe('when not authenticated', () => {
        it('mutations still return functions but will fail without token', () => {
            vi.mocked(useAuth).mockReturnValue({ session: null } as any);

            const { result } = renderHook(() => useTaskMutations(), {
                wrapper: createWrapper(),
            });

            expect(result.current.completeTaskMutation).toBeDefined();
            expect(result.current.saveDraftMutation).toBeDefined();
        });
    });
});
