import { z } from 'zod';

export const UserAccessSchema = z.object({
    access_token: z.string(),
    is_authenticated: z.boolean(),
    user_id: z.string(),
    user_message_count: z.number(),
    created_at: z.string(),
    updated_at: z.string(),
});
export type UserAccess = z.infer<typeof UserAccessSchema>;

export const UserAccessWithoutAccessTokenSchema = UserAccessSchema.omit({
    access_token: true,
});
export type UserAccessWithoutAccessToken = z.infer<typeof UserAccessWithoutAccessTokenSchema>;
