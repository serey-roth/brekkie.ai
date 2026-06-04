import { type UserAccess } from '@/data/schemas/user-access';
import { EventManager } from '@/utils/event-manager';

type UserAccessEvents = {
    accessEnsured: UserAccess;
    accessChanged: UserAccess | null;
};

export class UserAccessManager {
    private _userAccess: UserAccess | null = null;
    private _eventManager = new EventManager<UserAccessEvents>();

    isAccessEnsured(): boolean {
        return this._userAccess !== null;
    }

    getJwt(): string | null {
        return this._userAccess?.jwt ?? null;
    }

    getUserId(): string | null {
        return this._userAccess?.user_id ?? null;
    }

    getUserAccess(): UserAccess | null {
        return this._userAccess;
    }

    subscribe<K extends keyof UserAccessEvents>(
        event: K,
        callback: (payload: UserAccessEvents[K]) => void,
    ) {
        this._eventManager.subscribe(event, callback);
    }

    unsubscribe<K extends keyof UserAccessEvents>(
        event: K,
        callback: (payload: UserAccessEvents[K]) => void,
    ) {
        this._eventManager.unsubscribe(event, callback);
    }

    setAuth(userId: string, jwt: string) {
        const userAccess: UserAccess = { user_id: userId, jwt };
        this._userAccess = userAccess;
        this._eventManager.publish('accessEnsured', userAccess);
        this._eventManager.publish('accessChanged', userAccess);
    }

    clearAuth() {
        this._userAccess = null;
        this._eventManager.publish('accessChanged', null);
    }

    resetState() {
        this.clearAuth();
    }

    dispose() {
        this._eventManager.dispose();
    }
}
