import { DateTime } from 'luxon';
import type { Thread } from '@/data/schemas/threads';

export function formatThreadTimestamp(ts: string) {
    const dt = DateTime.fromISO(ts);
    const now = DateTime.now();

    if (dt.hasSame(now, 'day')) {
        return dt.toFormat('h:mm a');
    } else if (dt.hasSame(now.minus({ days: 1 }), 'day')) {
        return dt.toFormat('h:mm a');
    } else if (dt > now.minus({ days: 7 })) {
        return dt.toFormat('EEE h:mm a');
    } else if (dt > now.minus({ days: 30 })) {
        return dt.toFormat('MMM d h:mm a');
    } else {
        return dt.toFormat('MMM d, yyyy h:mm a');
    }
}

export function getThreadGroups(threads: Thread[]) {
    const now = DateTime.now();
    const groups = {
        today: [] as Thread[],
        yesterday: [] as Thread[],
        prev7: [] as Thread[],
        prev30: [] as Thread[],
        older: [] as Thread[],
    };

    threads.forEach((thread) => {
        const chatDate = DateTime.fromISO(thread.updated_at);
        const diff = now.diff(chatDate, 'days').days;

        if (chatDate.hasSame(now, 'day')) {
            groups.today.push(thread);
        } else if (chatDate.hasSame(now.minus({ days: 1 }), 'day')) {
            groups.yesterday.push(thread);
        } else if (diff <= 7) {
            groups.prev7.push(thread);
        } else if (diff <= 30) {
            groups.prev30.push(thread);
        } else {
            groups.older.push(thread);
        }
    });

    return [
        { label: 'Today', items: groups.today },
        { label: 'Yesterday', items: groups.yesterday },
        { label: 'This week', items: groups.prev7 },
        { label: 'This month', items: groups.prev30 },
        { label: 'Older', items: groups.older },
    ].filter((group) => group.items.length > 0);
}
