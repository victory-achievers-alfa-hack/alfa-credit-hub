import { useState } from 'react';
import { Button } from '@alfalab/core-components/button';
import { Typography } from '@alfalab/core-components/typography';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AutoContext';
import { useCredit } from '../context/CreditContext';
import { formatDateTime } from '../utils/format';

const clientLinks = [
  { to: '/client', label: 'Главная', end: true },
  { to: '/client/business', label: 'Мой бизнес' },
  { to: '/client/financing', label: 'Финансирование' },
  { to: '/client/applications', label: 'Мои заявки' },
];

const bankLinks = [
  { to: '/bank', label: 'Очередь заявок', end: true },
];

export function Header() {
  const { currentUser, logout } = useAuth();
  const { notifications, markNotificationRead, markAllNotificationsRead } = useCredit();
  const navigate = useNavigate();
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  if (!currentUser) return null;

  const links = currentUser.role === 'bank' ? bankLinks : clientLinks;
  const homePath = currentUser.role === 'bank' ? '/bank' : '/client';
  const profilePath = currentUser.role === 'bank' ? '/bank' : '/client/business';
  const clientNotifications = currentUser.role === 'client'
    ? notifications.filter((notification) => notification.companyId === currentUser.companyId)
    : [];
  const unreadCount = clientNotifications.filter((notification) => !notification.read).length;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const openNotification = (notificationId: string, applicationId: string) => {
    markNotificationRead(notificationId);
    setNotificationsOpen(false);
    navigate(`/client/applications/${applicationId}`);
  };

  return (
    <header className="app-header">
      <div className="app-header__inner">
        <button
          type="button"
          className="brand"
          onClick={() => navigate(homePath)}
          aria-label="На главную"
        >
          <span className="brand__mark">A</span>
          <span className="brand__copy">
            <strong>АЛЬФА / ПОТОК</strong>
            <small>{currentUser.role === 'bank' ? 'Рабочее место банка' : 'Кредитный кабинет'}</small>
          </span>
        </button>

        <nav className="app-nav" aria-label="Основная навигация">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => `app-nav__link${isActive ? ' app-nav__link--active' : ''}`}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="user-menu">
          {currentUser.role === 'client' && (
            <div className="notifications">
              <button
                type="button"
                className={`notifications__trigger${unreadCount > 0 ? ' notifications__trigger--unread' : ''}`}
                aria-label={unreadCount > 0 ? `Уведомления: ${unreadCount} новых` : 'Уведомления'}
                aria-expanded={notificationsOpen}
                onClick={() => setNotificationsOpen((open) => !open)}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />
                </svg>
                {unreadCount > 0 && <span>{unreadCount > 9 ? '9+' : unreadCount}</span>}
              </button>

              {notificationsOpen && (
                <div className="notifications-panel">
                  <div className="notifications-panel__header">
                    <div>
                      <strong>Уведомления</strong>
                      <small>{unreadCount > 0 ? `${unreadCount} новых` : 'Всё прочитано'}</small>
                    </div>
                    {unreadCount > 0 && currentUser.companyId && (
                      <button type="button" onClick={() => markAllNotificationsRead(currentUser.companyId ?? '')}>
                        Прочитать все
                      </button>
                    )}
                  </div>

                  <div className="notifications-panel__list">
                    {clientNotifications.length === 0 ? (
                      <div className="notifications-panel__empty">
                        <span>✓</span>
                        <strong>Новых событий нет</strong>
                        <small>Решения банка появятся здесь автоматически.</small>
                      </div>
                    ) : clientNotifications.slice(0, 6).map((notification) => (
                      <button
                        type="button"
                        className={`notification-item notification-item--${notification.tone}${notification.read ? '' : ' notification-item--unread'}`}
                        key={notification.id}
                        onClick={() => openNotification(notification.id, notification.applicationId)}
                      >
                        <span className="notification-item__marker" />
                        <span className="notification-item__copy">
                          <strong>{notification.title}</strong>
                          <span>{notification.message}</span>
                          <small>{formatDateTime(notification.createdAt)}</small>
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          <button
            type="button"
            className="user-menu__profile"
            onClick={() => {
              setNotificationsOpen(false);
              navigate(profilePath);
            }}
            title={currentUser.role === 'client' ? 'Открыть профиль бизнеса' : 'Открыть рабочий кабинет'}
          >
            <span className="user-menu__copy">
              <Typography.Text view="primary-small" weight="medium" tag="div">
                {currentUser.name}
              </Typography.Text>
              <Typography.Text view="secondary-small" color="secondary" tag="div">
                {currentUser.companyName}
              </Typography.Text>
            </span>
            <span className={`avatar${currentUser.role === 'bank' ? ' avatar--bank' : ''}`}>
              {currentUser.avatarText}
            </span>
          </button>

          <Button view="text" size={40} onClick={handleLogout} className="logout-button">
            Выйти
          </Button>
        </div>
      </div>
    </header>
  );
}
