import { ApiErrorSchema } from "@/data/schemas/errors";
import { UserAccessDataSchema, type UserAccessData } from "@/data/schemas/user-access";
import { type UserSigninPayload, type UserSignupPayload } from "@/data/schemas/users";

export interface IAuthClient {
    signin(payload: UserSigninPayload, accessToken: string | null): Promise<UserAccessData>;
    signup(payload: UserSignupPayload, accessToken: string | null): Promise<UserAccessData>;
    signout(accessToken: string | null): Promise<UserAccessData>;
}

export class HttpAuthClient implements IAuthClient {
    private _baseUrl: string;

    constructor(baseUrl: string) {
        this._baseUrl = baseUrl;
    }

    async signin(payload: UserSigninPayload, accessToken: string | null): Promise<UserAccessData> {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        } as Record<string, string>;

        if (accessToken) {
            headers['Authorization'] = `Bearer ${accessToken}`;
        }

        // TODO: Change API to /signin
        const response = await fetch(`${this._baseUrl}/auth/login`, {
            method: 'POST',
            headers,
            body: JSON.stringify(payload),
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

    async signup(payload: UserSignupPayload, accessToken: string | null): Promise<UserAccessData> {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        } as Record<string, string>;

        if (accessToken) {
            headers['Authorization'] = `Bearer ${accessToken}`;
        }

        const response = await fetch(`${this._baseUrl}/auth/signup`, {
            method: 'POST',
            headers,
            body: JSON.stringify(payload),
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

    async signout(accessToken: string | null): Promise<UserAccessData> {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        } as Record<string, string>;

        if (accessToken) {
            headers['Authorization'] = `Bearer ${accessToken}`;
        }

        // TODO: Change API to /signout
        const response = await fetch(`${this._baseUrl}/auth/logout`, {
            method: 'POST', 
            headers,
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