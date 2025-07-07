import { ApiErrorSchema } from '@/data/schemas/errors';
import { type UserAccessData, UserAccessDataSchema } from '@/data/schemas/user-access';

export interface IAccessTokenClient {
    ensureUserAccess(): Promise<UserAccessData>;
}

export class HttpAccessTokenClient implements IAccessTokenClient {
    private _baseUrl: string;

    constructor(baseUrl: string) {
        this._baseUrl = baseUrl;
    }

    async ensureUserAccess(): Promise<UserAccessData> {
        const headers = {
            'Content-Type': 'application/json',
            Accept: 'application/json',
        } as Record<string, string>;

        const response = await fetch(`${this._baseUrl}/access-token/ensure-access-token`, {
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

        const result = await UserAccessDataSchema.safeParseAsync(json);
        if (!result.success) {
            throw new Error(`Invalid response from server: ${JSON.stringify(json)}`);
        }

        return result.data;
    }
}
