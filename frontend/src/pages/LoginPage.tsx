import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SYNTHETIC_CLIENTS, type UserProfile } from '../data/mockData';

interface LoginPageProps {
  onLogin: (user: UserProfile) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLogin }) => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [showAlfaIdModal, setShowAlfaIdModal] = useState(false);

  // Вход для сотрудника банка (admin / admin)
  const handleBankLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (username.trim() === 'admin' && password.trim() === 'admin') {
      const bankUser: UserProfile = {
        id: 'bank-admin',
        role: 'bank',
        name: 'Андеррайтер: Кредитный отдел',
        companyName: 'АО «АЛЬФА-БАНК»',
        avatarText: 'АБ',
      };
      onLogin(bankUser);
      navigate('/bank');
    } else {
      setError('Неверный логин или пароль для служебного входа (подсказка: admin / admin)');
    }
  };

  // Вход за синтетического клиента через Альфа-ID
  const handleSelectClient = (client: UserProfile) => {
    onLogin(client);
    setShowAlfaIdModal(false);
    navigate('/client');
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#F3F4F7',
      padding: '20px',
      position: 'relative',
    }}>
      <div style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '20px',
        width: '100%',
        maxWidth: '440px',
        padding: '40px 36px',
        boxShadow: '0 12px 36px rgba(0,0,0,0.06)',
        border: '1px solid #E5E7EB',
      }}>
        {/* Логотип Альфа-Банка */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '28px' }}>
          <div style={{
            backgroundColor: '#EF3124',
            color: '#FFFFFF',
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 800,
            fontSize: '24px',
          }}>
            А
          </div>
          <div>
            <div style={{ fontSize: '18px', fontWeight: 800, letterSpacing: '-0.3px', color: '#0B1F35' }}>
              АЛЬФА-БАНК <span style={{ color: '#EF3124' }}>БИЗНЕС</span>
            </div>
            <div style={{ fontSize: '12px', color: '#6F7985' }}>
              Единый портал кредитного конвейера
            </div>
          </div>
        </div>

        {/* Форма для сотрудника банка */}
        <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '6px', color: '#0B1F35' }}>
          Вход для сотрудников банка
        </h2>
        <p style={{ fontSize: '12px', color: '#6F7985', marginBottom: '18px' }}>
          Для проверки конвейера используйте: <b style={{ color: '#0B1F35' }}>admin / admin</b>
        </p>

        <form onSubmit={handleBankLogin} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#333F48', marginBottom: '6px' }}>
              Логин
            </label>
            <input
              type="text"
              placeholder="admin"
              value={username}
              onChange={(e) => { setUsername(e.target.value); setError(''); }}
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: '8px',
                border: '1px solid #D0D5DD',
                fontSize: '14px',
                outline: 'none',
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#333F48', marginBottom: '6px' }}>
              Пароль
            </label>
            <input
              type="password"
              placeholder="•••••"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setError(''); }}
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: '8px',
                border: '1px solid #D0D5DD',
                fontSize: '14px',
                outline: 'none',
              }}
            />
          </div>

          {error && (
            <div style={{ fontSize: '12px', color: '#D9383A', backgroundColor: '#FDECEC', padding: '8px 12px', borderRadius: '6px' }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            style={{
              marginTop: '4px',
              backgroundColor: '#0B1F35',
              color: '#FFFFFF',
              border: 'none',
              padding: '12px',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'background 0.2s',
            }}
          >
            Войти как андеррайтер банка
          </button>
        </form>

        <div style={{ display: 'flex', alignItems: 'center', margin: '24px 0', gap: '12px' }}>
          <div style={{ flex: 1, height: '1px', backgroundColor: '#E5E7EB' }}></div>
          <span style={{ fontSize: '12px', color: '#8A94A6', textTransform: 'uppercase' }}>или</span>
          <div style={{ flex: 1, height: '1px', backgroundColor: '#E5E7EB' }}></div>
        </div>

        {/* Кнопка входа через Альфа-ID для предпринимателя */}
        <button
          type="button"
          onClick={() => setShowAlfaIdModal(true)}
          style={{
            width: '100%',
            backgroundColor: '#EF3124',
            color: '#FFFFFF',
            border: 'none',
            padding: '14px',
            borderRadius: '10px',
            fontSize: '14px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
            boxShadow: '0 4px 14px rgba(239, 49, 36, 0.25)',
          }}
        >
          <span style={{
            backgroundColor: '#FFF',
            color: '#EF3124',
            borderRadius: '4px',
            padding: '1px 6px',
            fontWeight: 900,
            fontSize: '12px',
          }}>
            А
          </span>
          Войти с Альфа-ID (Клиент)
        </button>
      </div>

      {/* Модальное окно выбора синтетического клиента */}
      {showAlfaIdModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(11, 31, 53, 0.6)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px',
        }}>
          <div style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '16px',
            maxWidth: '480px',
            width: '100%',
            padding: '28px',
            boxShadow: '0 20px 40px rgba(0,0,0,0.15)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#0B1F35' }}>
                  Вход через Альфа-ID
                </h3>
                <p style={{ fontSize: '12px', color: '#6F7985' }}>
                  Выберите профиль предпринимателя из синтетической базы
                </p>
              </div>
              <button
                onClick={() => setShowAlfaIdModal(false)}
                style={{ background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer', color: '#8A94A6' }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {SYNTHETIC_CLIENTS.map((client) => (
                <div
                  key={client.id}
                  onClick={() => handleSelectClient(client)}
                  style={{
                    padding: '12px 16px',
                    borderRadius: '10px',
                    border: '1px solid #E5E7EB',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '14px',
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#EF3124';
                    e.currentTarget.style.backgroundColor = '#FFF8F8';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = '#E5E7EB';
                    e.currentTarget.style.backgroundColor = '#FFFFFF';
                  }}
                >
                  <div style={{
                    width: '38px',
                    height: '38px',
                    borderRadius: '50%',
                    backgroundColor: '#0B1F35',
                    color: '#FFF',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: '13px',
                  }}>
                    {client.avatarText}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '14px', fontWeight: 700, color: '#0B1F35' }}>
                      {client.name}
                    </div>
                    <div style={{ fontSize: '12px', color: '#6F7985' }}>
                      {client.companyName} • ИНН {client.inn}
                    </div>
                  </div>
                  <span style={{ color: '#EF3124', fontWeight: 600, fontSize: '13px' }}>Выбрать →</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
