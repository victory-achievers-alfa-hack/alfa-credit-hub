import { Button } from '@alfalab/core-components/button';
import { Typography } from '@alfalab/core-components/typography';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AutoContext';

export function NotFoundPage() {
  const navigate = useNavigate();
  const { currentUser } = useAuth();

  return (
    <main className="not-found">
      <span className="not-found__code">404</span>
      <Typography.Title tag="h1" view="large" weight="bold">Страница не найдена</Typography.Title>
      <p>Возможно, адрес изменился или у вашего профиля нет доступа к этому разделу.</p>
      <Button
        view="accent"
        size={48}
        onClick={() => navigate(!currentUser ? '/login' : currentUser.role === 'bank' ? '/bank' : '/client')}
      >
        Вернуться на главную
      </Button>
    </main>
  );
}
