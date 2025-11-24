/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Task } from '../models/Task';
import type { TaskCreate } from '../models/TaskCreate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class TasksService {
    /**
     * Draft Tasks
     * @param requestBody
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static draftTasks(
        requestBody: Array<TaskCreate>,
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/tasks/draft',
            headers: {
                'authorization': authorization,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Today Tasks
     * @param authorization
     * @returns Task Successful Response
     * @throws ApiError
     */
    public static getTodayTasks(
        authorization?: (string | null),
    ): CancelablePromise<Array<Task>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/tasks/today',
            headers: {
                'authorization': authorization,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Complete Task
     * @param taskId
     * @param proofUrl
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static completeTask(
        taskId: string,
        proofUrl?: string,
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/tasks/{task_id}/complete',
            path: {
                'task_id': taskId,
            },
            headers: {
                'authorization': authorization,
            },
            query: {
                'proof_url': proofUrl,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
