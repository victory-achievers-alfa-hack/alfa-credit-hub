import { useState, type FormEvent } from 'react';
import { Button } from '@alfalab/core-components/button';
import { Input } from '@alfalab/core-components/input';
import { Typography } from '@alfalab/core-components/typography';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AutoContext';
import { DEMO_USERS } from '../data/mockData';

const EMAIL_PATTERN = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;

export function LoginPage() {
  const { currentUser, login, loginAs } = useAuth();
  const [email, setEmail] = useState('client@demo.ru');
  const [password, setPassword] = useState('123456');
  const [emailError, setEmailError] = useState('');
  const [authError, setAuthError] = useState('');

  if (currentUser) {
    return <Navigate to={currentUser.role === 'bank' ? '/bank' : '/client'} replace />;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();

    if (!EMAIL_PATTERN.test(email)) {
      setEmailError('Введите корректный email латиницей');
      return;
    }

    const result = await login(email, password);
    if (!result.success) {
      setAuthError(result.message ?? 'Не удалось войти');
      return;
    }

    // The server profile determines the destination through Navigate above.
  };

  const handleQuickLogin = async (userId: string) => {
    const result = await loginAs(userId);
    if (!result.success) { setAuthError(result.message ?? 'Не удалось войти'); return; }

  };

  return (
    <main className="login-page">
      <section className="login-story">
        <div className="login-story__brand">
          <span className="brand__mark brand__mark--large">A</span>
          <span>АЛЬФА / ПОТОК</span>
        </div>
        <div className="login-story__content">
          <span className="login-story__chip">Умный кредитный кабинет</span>
          <Typography.Title tag="h1" view="xlarge" weight="bold" className="login-story__title">
            Финансирование бизнеса без лишних шагов
          </Typography.Title>
          <Typography.Text tag="p" view="primary-large" className="login-story__text">
            Банк уже знает компанию, подбирает подходящие условия и прозрачно проводит заявку до выдачи.
          </Typography.Text>
          <div className="login-story__steps">
            <span><b>01</b> Выберите цель</span>
            <span><b>02</b> Получите расчёт</span>
            <span><b>03</b> Следите за решением</span>
          </div>
        </div>
        <div className="login-story__glow" />
      </section>

      <section className="login-panel">
        <div className="login-card">
          <div className="login-card__heading">
            <div className="eyebrow">Демонстрационный контур</div>
            <Typography.Title tag="h2" view="medium" weight="bold">Войти в кабинет</Typography.Title>
            <Typography.Text tag="p" view="primary-small" color="secondary">
              Используйте тестовый аккаунт или выберите готовый профиль ниже.
            </Typography.Text>
          </div>

          <form className="login-form" onSubmit={handleSubmit}>
            <Input
              label="Электронная почта"
              labelView="outer"
              type="email"
              size={56}
              block
              value={email}
              maxLength={80}
              autoComplete="username"
              spellCheck={false}
              error={emailError || false}
              hint="Только латинские буквы, цифры и символы email"
              onBlur={() => {
                if (email && !EMAIL_PATTERN.test(email)) setEmailError('Введите корректный email латиницей');
              }}
              onChange={(_, payload) => {
                const sanitizedEmail = payload.value.replace(/[^A-Za-z0-9@._%+-]/g, '');
                setEmail(sanitizedEmail);
                setAuthError('');
                setEmailError(payload.value === sanitizedEmail ? '' : 'Email можно вводить только латиницей');
              }}
            />
            <Input
              label="Пароль"
              labelView="outer"
              type="password"
              size={56}
              block
              value={password}
              autoComplete="current-password"
              onChange={(_, payload) => { setPassword(payload.value); setAuthError(''); }}
              error={authError || false}
            />
            <Button type="submit" view="accent" size={56} block>
              Войти
            </Button>
          </form>

          <div className="demo-divider"><span>Быстрый вход</span></div>

          <div className="demo-users">
            {DEMO_USERS.map((user) => (
              <button
                type="button"
                className="demo-user"
                key={user.id}
                onClick={() => handleQuickLogin(user.id)}
              >
                <span className={`avatar${user.role === 'bank' ? ' avatar--bank' : ''}`}>{user.avatarText}</span>
                <span className="demo-user__copy">
                  <strong>{user.companyName}</strong>
                  <small>{user.email} · {user.role === 'bank' ? 'Сотрудник банка' : 'Предприниматель'}</small>
                </span>
                <span className="demo-user__arrow">→</span>
              </button>
            ))}
          </div>

          <div className="login-card__hint">Пароль для всех тестовых аккаунтов: <b>123456</b></div>
        </div>
      </section>
    </main>
  );
}
