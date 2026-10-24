import type { ClientNotification, CreditApplication } from '../../types/credit';

export type RealtimeEvent =
  | {
      type: 'application.updated';
      payload: { application: CreditApplication };
    }
  | {
      type: 'notification.created';
      payload: { notification: ClientNotification };
    }
  | {
      type: 'notification.read';
      payload: { notificationId: string };
    };

export type RealtimeServerEvent = RealtimeEvent | {
  type: 'connection.ready';
  payload: { clientId: string };
};

export type RealtimeEnvelope<T extends RealtimeServerEvent = RealtimeServerEvent> = T & {
  id: string;
  sentAt: string;
};
