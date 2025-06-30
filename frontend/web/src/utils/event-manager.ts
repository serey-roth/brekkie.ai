export type EventsMap = Record<string, unknown>;

export type EventCallback<T> = (data: T) => void;

export class EventManager<Events extends EventsMap> {
    private listeners: {
        [K in keyof Events]?: Set<EventCallback<Events[K]>>;
    } = {};

    subscribe<K extends keyof Events>(event: K, callback: EventCallback<Events[K]>) {
        if (!this.listeners[event]) {
            this.listeners[event] = new Set();
        }
        this.listeners[event]!.add(callback);
    }

    unsubscribe<K extends keyof Events>(event: K, callback: EventCallback<Events[K]>) {
        this.listeners[event]?.delete(callback);
    }

    publish<K extends keyof Events>(event: K, data: Events[K]) {
        this.listeners[event]?.forEach(cb => cb(data));
    }

    dispose(event?: keyof Events) {
        if (event) {
            delete this.listeners[event];
        } else {
            this.listeners = {};
        }
    }
}
