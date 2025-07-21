import { ApiErrorSchema } from '@/data/schemas/errors';
import { type UserAccess, UserAccessSchema } from '@/data/schemas/user-access';

export interface IUserAccessApiClient {
    ensureUserAccess(): Promise<UserAccess>;
    resetUserAccess(): Promise<UserAccess>;
}

export class UserAccessApiClient implements IUserAccessApiClient {
    private _baseUrl: string;

    constructor(baseUrl: string) {
        this._baseUrl = baseUrl;
    }

    async ensureUserAccess(): Promise<UserAccess> {
        const headers = {
            'Content-Type': 'application/json',
            Accept: 'application/json',
        } as Record<string, string>;

        const response = await fetch(`${this._baseUrl}/access/ensure-access`, {
            method: 'POST',
            headers,
            credentials: 'include',
        });

        const json = await response.json();

        if (!response.ok) {
            const errorResult = await ApiErrorSchema.safeParseAsync(json);
            if (errorResult.success) {
                throw new Error(errorResult.data.detail.message);
            }
            throw new Error(`${json.detail.message || response.statusText}`);
        }

        const result = await UserAccessSchema.safeParseAsync(json);
        if (!result.success) {
            throw new Error(`Invalid response from server: ${JSON.stringify(json)}`);
        }

        return result.data;
    }

    async resetUserAccess(): Promise<UserAccess> {
        const headers = {
            'Content-Type': 'application/json',
            Accept: 'application/json',
        } as Record<string, string>;

        const response = await fetch(`${this._baseUrl}/access/reset-access`, {
            method: 'POST',
            headers,
            credentials: 'include',
        });

        if (!response.ok) {
            const json = await response.json();
            const errorResult = await ApiErrorSchema.safeParseAsync(json);
            if (errorResult.success) {
                throw new Error(errorResult.data.detail.message);
            }
            throw new Error(`${json.detail.message || response.statusText}`);
        }

        const json = await response.json();
        const result = await UserAccessSchema.safeParseAsync(json);
        if (!result.success) {
            throw new Error(`Invalid response from server: ${JSON.stringify(json)}`);
        }

        return result.data;
    }
}
