import type { ClientNotification, CreditApplication } from '../../types/credit';

export type RealtimeServerEvent =
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

export type RealtimeEnvelope = RealtimeServerEvent & {
  id: string;
  sentAt: string;
};
