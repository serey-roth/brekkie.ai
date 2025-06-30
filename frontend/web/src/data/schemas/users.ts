import { z } from 'zod';

export const UserLoginSchema = z.object({
    email: z.string().email("Invalid email address"),
    password: z.string(),
});
export type UserSigninPayload = z.infer<typeof UserLoginSchema>;

export const UserSignupSchema = z.object({
    email: z.string().email("Invalid email address"),
    name: z.string().min(1, "Name is required"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string().min(8, "Password must be at least 8 characters"),
}).refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
});
export type UserSignupPayload = z.infer<typeof UserSignupSchema>;
