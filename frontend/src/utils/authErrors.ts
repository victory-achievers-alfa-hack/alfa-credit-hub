export type AuthErrorKind = 'credentials' | 'connection' | 'other';
type AuthOperation = 'login' | 'logout' | 'session';

export function getAuthFailure(error: unknown, operation: AuthOperation) {
  const status = typeof error === 'object' && error !== null && 'status' in error
    && typeof error.status === 'number' ? error.status : undefined;
  let kind: AuthErrorKind = 'other';
  let message: string;

  if (status === 0) {
    kind = 'connection';
    message = 'Нет подключения к серверу. Проверьте соединение и попробуйте ещё раз.';
  } else if (status !== undefined && status >= 500) {
    kind = 'connection';
    message = 'Сервис временно недоступен. Попробуйте ещё раз позже.';
  } else if (status === 401 && operation === 'login') {
    kind = 'credentials';
    message = 'Неверная почта или пароль.';
  } else {
    message = operation === 'session'
      ? 'Не удалось проверить сессию. Попробуйте войти ещё раз.'
      : operation === 'logout'
        ? 'Повторите попытку позже.'
        : error instanceof Error ? error.message : 'Не удалось войти. Повторите попытку.';
  }

  if (operation === 'logout') {
    message = `Не удалось выйти. ${message} Сессия не завершена.`;
  }
  return { kind, message };
}
