import { z } from 'zod';

export const UserAccessDataSchema = z.object({
    access_token: z.string(),
    is_authenticated: z.boolean(),
    user_id: z.string(),
    email: z.string().nullable(),
    name: z.string().nullable(),
    user_message_count: z.number(),
});
export type UserAccessData = z.infer<typeof UserAccessDataSchema>;

export const UserAccessDataWithoutAccessTokenSchema = UserAccessDataSchema.omit({
    access_token: true,
});
export type UserAccessDataWithoutAccessToken = z.infer<
    typeof UserAccessDataWithoutAccessTokenSchema
>;
