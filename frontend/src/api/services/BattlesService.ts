/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BattleInvite } from '../models/BattleInvite';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class BattlesService {
    /**
     * Get Current Battle
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getCurrentBattle(
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/battles/current',
            headers: {
                'authorization': authorization,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Invites
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getInvites(
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/battles/invites',
            headers: {
                'authorization': authorization,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Invite User
     * @param requestBody
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static inviteUser(
        requestBody: BattleInvite,
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/battles/invite',
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
     * Accept Battle
     * @param battleId
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static acceptBattle(
        battleId: string,
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/battles/{battle_id}/accept',
            path: {
                'battle_id': battleId,
            },
            headers: {
                'authorization': authorization,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Reject Battle
     * @param battleId
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static rejectBattle(
        battleId: string,
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/battles/{battle_id}/reject',
            path: {
                'battle_id': battleId,
            },
            headers: {
                'authorization': authorization,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
