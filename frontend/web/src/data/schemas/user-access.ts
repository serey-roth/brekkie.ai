import { z } from 'zod';

export const UserAccessSchema = z.object({
    user_id: z.string(),
    jwt: z.string(),
});
export type UserAccess = z.infer<typeof UserAccessSchema>;
