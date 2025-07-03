import { ApiErrorSchema } from "@/data/schemas/errors";
import { GetUserRecipesResponseSchema, type GetUserRecipesResponse } from "@/data/schemas/recipes";

export interface IRecipesClient {
    getUserRecipes(accessToken: string | null): Promise<GetUserRecipesResponse>;
}

export class HttpRecipesClient implements IRecipesClient {
    private _baseUrl: string;

    constructor(baseUrl: string) {
        this._baseUrl = baseUrl;
    }

    async getUserRecipes(accessToken: string | null): Promise<GetUserRecipesResponse> {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        } as Record<string, string>;

        if (accessToken) {
            headers['Authorization'] = `Bearer ${accessToken}`;
        }

        const url = new URL(`${this._baseUrl}/recipes`);

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

        const result = await GetUserRecipesResponseSchema.safeParseAsync(json);
        if (!result.success) {
            throw new Error(`Invalid response from server: ${JSON.stringify(json)}`);
        }

        return result.data;
    }   
}
