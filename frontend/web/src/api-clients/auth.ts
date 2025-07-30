import {
    supabase,
    type AuthChangeEvent,
    type Session,
    type Subscription,
    type User,
    type JwtPayload,
} from '@/supabase-client';

export interface ISupabaseAuthApiClient {
    googleLogin(): Promise<string>;
    emailLogin(
        email: string,
        password: string,
    ): Promise<{ user: User | null; session: Session | null }>;
    emailSignUp(
        email: string,
        password: string,
    ): Promise<{ user: User | null; session: Session | null }>;
    resetPassword(email: string): Promise<void>;
    logout(): Promise<void>;
    getSession(): Promise<Session | null>;
    getUser(): Promise<User>;
    getClaims(): Promise<JwtPayload>;
    listenForAuthStateChanges(
        callback: (event: AuthChangeEvent, session: Session | null) => void,
    ): { data: { subscription: Subscription } };
}

export class SupabaseAuthApiClient implements ISupabaseAuthApiClient {
    async googleLogin(redirectTo?: string): Promise<string> {
        const { data, error } = await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: redirectTo ?? `${window.location.origin}/auth/callback`,
            },
        });
        if (error) {
            throw new Error(error.message);
        }
        return data.url;
    }

    async emailLogin(
        email: string,
        password: string,
    ): Promise<{ user: User | null; session: Session | null }> {
        const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password,
        });
        if (error) {
            throw new Error(error.message);
        }
        return data;
    }

    async emailSignUp(
        email: string,
        password: string,
    ): Promise<{ user: User | null; session: Session | null }> {
        const { data, error } = await supabase.auth.signUp({
            email,
            password,
        });
        if (error) {
            throw new Error(error.message);
        }
        return data;
    }

    async resetPassword(email: string): Promise<void> {
        const { error } = await supabase.auth.resetPasswordForEmail(email, {
            redirectTo: `${window.location.origin}/auth/callback`,
        });
        if (error) {
            throw new Error(error.message);
        }
    }

    async logout(): Promise<void> {
        const { error } = await supabase.auth.signOut();
        if (error) {
            throw new Error(error.message);
        }
    }

    async getSession(): Promise<Session | null> {
        const { data, error } = await supabase.auth.getSession();
        if (error) {
            throw new Error(error.message);
        }
        return data.session;
    }

    async getUser(): Promise<User> {
        const { data, error } = await supabase.auth.getUser();
        if (error) {
            throw new Error(error.message);
        }
        return data.user;
    }

    async getClaims(): Promise<JwtPayload> {
        const { data, error } = await supabase.auth.getClaims();
        if (error) {
            throw new Error(error.message);
        }
        if (!data?.claims) {
            throw new Error('No claims found');
        }
        return data.claims;
    }

    listenForAuthStateChanges(
        callback: (event: AuthChangeEvent, session: Session | null) => void,
    ): { data: { subscription: Subscription } } {
        return supabase.auth.onAuthStateChange(callback);
    }
}
