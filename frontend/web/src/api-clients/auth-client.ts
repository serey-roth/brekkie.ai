import { ApiErrorSchema } from '@/data/schemas/errors';
import { UserAccessDataSchema, type UserAccessData } from '@/data/schemas/user-access';
import { type UserSigninPayload, type UserSignupPayload } from '@/data/schemas/users';

export interface IAuthClient {
    signin(payload: UserSigninPayload): Promise<UserAccessData>;
    signup(payload: UserSignupPayload): Promise<UserAccessData>;
    signout(): Promise<UserAccessData>;
}

export class HttpAuthClient implements IAuthClient {
    private _baseUrl: string;

    constructor(baseUrl: string) {
        this._baseUrl = baseUrl;
    }

    async signin(payload: UserSigninPayload): Promise<UserAccessData> {
        const headers = {
            'Content-Type': 'application/json',
            Accept: 'application/json',
        } as Record<string, string>;

        const response = await fetch(`${this._baseUrl}/auth/login`, {
            method: 'POST',
            headers,
            body: JSON.stringify(payload),
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
            throw new Error('Invalid response format from server');
        }

        return result.data;
    }

    async signup(payload: UserSignupPayload): Promise<UserAccessData> {
        const headers = {
            'Content-Type': 'application/json',
            Accept: 'application/json',
        } as Record<string, string>;

        const response = await fetch(`${this._baseUrl}/auth/signup`, {
            method: 'POST',
            headers,
            body: JSON.stringify(payload),
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

    async signout(): Promise<UserAccessData> {
        const headers = {
            'Content-Type': 'application/json',
            Accept: 'application/json',
        } as Record<string, string>;

        // TODO: Change API to /signout
        const response = await fetch(`${this._baseUrl}/auth/logout`, {
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
