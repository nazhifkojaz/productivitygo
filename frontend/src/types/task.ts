/**
 * Task type definition
 */
export interface Task {
    id: string;
    content: string;
    is_completed: boolean;
    is_optional: boolean;
    assigned_score: number;
}

/**
 * Task creation type
 */
export interface TaskCreate {
    content: string;
    is_optional: boolean;
    assigned_score: number;
}
