import type { IAccessTokenClient } from '@/api-clients/access-token-client';
import { type UserAccessData } from '@/data/schemas/user-access';
import { EventManager } from '@/utils/event-manager';

type UserAccessEvents = {
    accessEnsured: UserAccessData;
    accessChanged: UserAccessData | null;
    limitReached: string;
    errorOccurred: string;
};

type UserAccessManagerConfig = {
    maxMessageCountAnonymous: number;
    maxMessageCountAuthenticated: number;
};

export class UserAccessManager {
    private _accessData: UserAccessData | null = null;
    private _accessTokenClient: IAccessTokenClient;
    private _eventManager = new EventManager<UserAccessEvents>();
    private _config: UserAccessManagerConfig;

    constructor(accessTokenClient: IAccessTokenClient, config: UserAccessManagerConfig) {
        this._accessTokenClient = accessTokenClient;
        this._config = config;
    }

    isAccessEnsured(): boolean {
        return this._accessData !== null;
    }

    getAccessToken(): string | null {
        return this._accessData?.access_token ?? null;
    }

    getUserId(): string | null {
        return this._accessData?.user_id ?? null;
    }

    getUserAccessData(): UserAccessData | null {
        return this._accessData;
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

    setUserAccessData(accessData: UserAccessData) {
        this._accessData = accessData;
        this._eventManager.publish('accessChanged', accessData);
    }

    isAuthenticated(): boolean | null {
        return this._accessData?.is_authenticated ?? null;
    }

    getUserMessageCount(): number | null {
        return this._accessData?.user_message_count ?? null;
    }

    optimisticIncrementUserMessageCount() {
        if (this._accessData) {
            this._accessData.user_message_count++;
            this._eventManager.publish('accessChanged', this._accessData);
        }
    }

    hasReachedMessageLimit(userAccessData: UserAccessData): boolean | null {
        const messageCount = userAccessData.user_message_count;
        const messageLimit = userAccessData.is_authenticated
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

    async ensureUserAccess() {
        try {
            const accessData = await this._accessTokenClient.ensureUserAccess();
            this._accessData = accessData;
            this._eventManager.publish('accessEnsured', accessData);
        } catch (error) {
            this._eventManager.publish('errorOccurred', error as string);
        }
    }

    resetState() {
        this._accessData = null;
    }

    dispose() {
        this._eventManager.dispose();
    }
}
