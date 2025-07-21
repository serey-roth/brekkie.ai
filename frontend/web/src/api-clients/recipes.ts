import { ApiErrorSchema } from '@/data/schemas/errors';
import { GetUserRecipesResponseSchema, type GetUserRecipesResponse } from '@/data/schemas/recipes';

export interface IRecipesClient {
    getUserRecipes(): Promise<GetUserRecipesResponse>;
}

export class RecipesApiClient implements IRecipesClient {
    private _baseUrl: string;

    constructor(baseUrl: string) {
        this._baseUrl = baseUrl;
    }

    async getUserRecipes(): Promise<GetUserRecipesResponse> {
        const headers = {
            'Content-Type': 'application/json',
            Accept: 'application/json',
        } as Record<string, string>;

        const url = new URL(`${this._baseUrl}/recipes`);

        const response = await fetch(url.toString(), {
            method: 'GET',
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

        const result = await GetUserRecipesResponseSchema.safeParseAsync(json);
        if (!result.success) {
            throw new Error(`Invalid response from server: ${JSON.stringify(json)}`);
        }

        return result.data;
    }
}
