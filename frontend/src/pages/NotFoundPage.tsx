import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AutoContext';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();
  const { currentUser } = useAuth();

  const handleBack = () => {
    if (!currentUser) {
      navigate('/login');
    } else {
      navigate(currentUser.role === 'bank' ? '/bank' : '/client');
    }
  };

  return (
    <div style={{
      minHeight: '80vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      textAlign: 'center',
      padding: '20px'
    }}>
      <div style={{
        fontSize: '100px',
        fontWeight: 900,
        color: '#EF3124',
        lineHeight: 1,
        marginBottom: '16px'
      }}>
        404
      </div>
      <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#0B1F35', marginBottom: '8px' }}>
        Страница не найдена
      </h1>
      <p style={{ color: '#6F7985', fontSize: '15px', maxWidth: '420px', marginBottom: '24px' }}>
        Кажется, такой страницы в кредитном кабинете нет или у вас нет к ней доступа.
      </p>
      <button
        onClick={handleBack}
        style={{
          backgroundColor: '#0B1F35',
          color: '#FFFFFF',
          border: 'none',
          padding: '12px 28px',
          borderRadius: '8px',
          fontSize: '14px',
          fontWeight: 600,
          cursor: 'pointer'
        }}
      >
        Вернуться на главную
      </button>
    </div>
  );
};
