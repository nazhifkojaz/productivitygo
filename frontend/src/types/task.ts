/**
 * Task category type - determines attack element against monsters
 */
export type TaskCategory =
    | 'errand'
    | 'focus'
    | 'physical'
    | 'creative'
    | 'social'
    | 'wellness'
    | 'organization';

/**
 * Task category metadata for UI display
 */
export const TASK_CATEGORIES = [
    {
        key: 'errand',
        label: 'Errand',
        element: 'Normal',
        emoji: '📋',
        description: 'Groceries, chores, appointments, laundry',
    },
    {
        key: 'focus',
        label: 'Focus',
        element: 'Arcane',
        emoji: '🔮',
        description: 'Deep work, coding, writing, studying',
    },
    {
        key: 'physical',
        label: 'Physical',
        element: 'Strength',
        emoji: '💪',
        description: 'Exercise, sports, deep-cleaning',
    },
    {
        key: 'creative',
        label: 'Creative',
        element: 'Fire',
        emoji: '🔥',
        description: 'Design, art, music, content creation',
    },
    {
        key: 'social',
        label: 'Social',
        element: 'Light',
        emoji: '✨',
        description: 'Meetings, networking, calls, emails',
    },
    {
        key: 'wellness',
        label: 'Wellness',
        element: 'Nature',
        emoji: '🌿',
        description: 'Meditation, healthy cooking, self-care',
    },
    {
        key: 'organization',
        label: 'Organization',
        element: 'Earth',
        emoji: '🪨',
        description: 'Planning, admin, budgeting, filing',
    },
] as const;

/**
 * Helper to get category metadata by key
 */
export const getTaskCategoryMeta = (category: TaskCategory) =>
    TASK_CATEGORIES.find((c) => c.key === category) ?? TASK_CATEGORIES[0];

/**
 * Task type definition
 */
export interface Task {
    id: string;
    content: string;
    is_completed: boolean;
    is_optional: boolean;
    category: TaskCategory;
}

/**
 * Task creation type
 */
export interface TaskCreate {
    content: string;
    is_optional: boolean;
    category?: TaskCategory;
}
