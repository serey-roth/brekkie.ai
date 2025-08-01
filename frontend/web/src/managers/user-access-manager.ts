import type { IUserAccessApiClient } from '@/api-clients/user-access';
import { type UserAccess } from '@/data/schemas/user-access';
import { EventManager } from '@/utils/event-manager';

type UserAccessEvents = {
    accessEnsured: UserAccess;
    accessChanged: UserAccess | null;
    limitReached: string;
    errorOccurred: string;
};

type UserAccessManagerConfig = {
    maxMessageCountAnonymous: number;
    maxMessageCountAuthenticated: number;
};

export class UserAccessManager {
    private _userAccess: UserAccess | null = null;
    private _userAccessApiClient: IUserAccessApiClient;
    private _eventManager = new EventManager<UserAccessEvents>();
    private _config: UserAccessManagerConfig;

    constructor(userAccessApiClient: IUserAccessApiClient, config: UserAccessManagerConfig) {
        this._userAccessApiClient = userAccessApiClient;
        this._config = config;
    }

    isAccessEnsured(): boolean {
        return this._userAccess !== null;
    }

    getAccessToken(): string | null {
        return this._userAccess?.access_token ?? null;
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

    setUserAccess(userAccess: UserAccess | null) {
        this._userAccess = userAccess;
        this._eventManager.publish('accessChanged', userAccess);
    }

    isAuthenticated(): boolean | null {
        return this._userAccess?.is_authenticated ?? null;
    }

    getUserMessageCount(): number | null {
        return this._userAccess?.user_message_count ?? null;
    }

    optimisticIncrementUserMessageCount() {
        if (this._userAccess) {
            this._userAccess.user_message_count++;
            this._eventManager.publish('accessChanged', this._userAccess);
        }
    }

    hasReachedMessageLimit(userAccess: UserAccess): boolean | null {
        const messageCount = userAccess.user_message_count;
        const messageLimit = userAccess.is_authenticated
            ? this._config.maxMessageCountAuthenticated
            : this._config.maxMessageCountAnonymous;
        return messageCount >= messageLimit;
    }

    getMessageLimit(): number {
        const isAuthenticated = this.isAuthenticated();
        if (isAuthenticated === null) {
            return this._config.maxMessageCountAnonymous;
        }
        return isAuthenticated
            ? this._config.maxMessageCountAuthenticated
            : this._config.maxMessageCountAnonymous;
    }

    async ensureAccess() {
        try {
            const accessData = await this._userAccessApiClient.ensureAccess();
            this.setUserAccess(accessData);
            this._eventManager.publish('accessEnsured', accessData);
        } catch (error) {
            this.setUserAccess(null);
            this._eventManager.publish(
                'errorOccurred',
                error instanceof Error ? error.message : 'Something went wrong. Please try again.',
            );
        }
    }

    async revokeAccess() {
        try {
            await this._userAccessApiClient.revokeAccess();
            this.setUserAccess(null);
        } catch (error) {
            this._eventManager.publish(
                'errorOccurred',
                error instanceof Error ? error.message : 'Something went wrong. Please try again.',
            );
        }
    }

    resetState() {
        this.setUserAccess(null);
    }

    dispose() {
        this._eventManager.dispose();
    }
}
