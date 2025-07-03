import { ApiErrorSchema } from "@/data/schemas/errors";
import { GetThreadMessagesResponseSchema, type GetThreadMessagesPayload, type GetThreadMessagesResponse } from "@/data/schemas/messages";
import { PaginatedThreadsSchema, type GetUserThreadsPayload, type PaginatedThreads } from "@/data/schemas/threads";

export interface IThreadsClient {
    getUserThreads(payload: GetUserThreadsPayload, accessToken: string | null): Promise<PaginatedThreads>;
    getThreadMessages(payload: GetThreadMessagesPayload, accessToken: string | null): Promise<GetThreadMessagesResponse>;
}

export class HttpThreadsClient implements IThreadsClient {
    private _baseUrl: string;

    constructor(baseUrl: string) {
        this._baseUrl = baseUrl;
    }

    async getUserThreads(payload: GetUserThreadsPayload, accessToken: string | null): Promise<PaginatedThreads> {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        } as Record<string, string>;

        if (accessToken) {
            headers['Authorization'] = `Bearer ${accessToken}`;
        }

        const url = new URL(`${this._baseUrl}/threads`);
        if (payload.limit) {
            url.searchParams.set('limit', payload.limit.toString());
        }
        if (payload.from_timestamp) {
            url.searchParams.set('from_timestamp', payload.from_timestamp);
        }
        if (payload.sort_by) {
            url.searchParams.set('sort_by', payload.sort_by);
        }
        if (payload.sort_order) {
            url.searchParams.set('sort_order', payload.sort_order);
        }
        if (payload.exclude_empty) {
            url.searchParams.set('exclude_empty', payload.exclude_empty.toString());
        }

        const response = await fetch(url.toString(), {
            method: 'GET',
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

        const result = await PaginatedThreadsSchema.safeParseAsync(json);
        if (!result.success) {
            throw new Error(`Invalid response from server: ${JSON.stringify(json)}`);
        }

        return result.data;
    }   

    async getThreadMessages(payload: GetThreadMessagesPayload, accessToken: string | null): Promise<GetThreadMessagesResponse> {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        } as Record<string, string>;
        
        if (accessToken) {
            headers['Authorization'] = `Bearer ${accessToken}`;
        }

        const url = new URL(`${this._baseUrl}/threads/${payload.thread_id}/messages`);
        if (payload.limit) {
            url.searchParams.set('limit', payload.limit.toString());
        }
        if (payload.from_timestamp) {
            url.searchParams.set('from_timestamp', payload.from_timestamp);
        }
        if (payload.sort_by) {
            url.searchParams.set('sort_by', payload.sort_by);
        }
        if (payload.sort_order) {
            url.searchParams.set('sort_order', payload.sort_order);
        }

        const response = await fetch(url.toString(), {
            method: 'GET',
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

        const result = await GetThreadMessagesResponseSchema.safeParseAsync(json);
        if (!result.success) {
            throw new Error(`Invalid response from server: ${JSON.stringify(json)}`);
        }

        return result.data;
    }
}