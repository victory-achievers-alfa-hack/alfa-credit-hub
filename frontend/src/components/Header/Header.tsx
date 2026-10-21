import React from 'react';
import { useNavigate } from 'react-router-dom';
import type { UserProfile } from '../data/mockData';

interface HeaderProps {
  currentUser: UserProfile | null;
  onLogout: () => void;
}

export const Header: React.FC<HeaderProps> = ({ currentUser, onLogout }) => {
  const navigate = useNavigate();

  if (!currentUser) return null;

  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '12px 32px',
      backgroundColor: '#FFFFFF',
      borderBottom: '1px solid #E4E6EB',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      {/* Логотип */}
      <div
        style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
        onClick={() => navigate(currentUser.role === 'bank' ? '/bank' : '/client')}
      >
        <div style={{
          backgroundColor: '#EF3124',
          color: '#FFFFFF',
          width: '34px',
          height: '34px',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 800,
          fontSize: '18px',
        }}>
          А
        </div>
        <div>
          <div style={{ fontSize: '15px', fontWeight: 800, color: '#0B1F35' }}>
            АЛЬФА-БАНК <span style={{ color: '#EF3124' }}>БИЗНЕС</span>
          </div>
          <div style={{ fontSize: '11px', color: '#6F7985' }}>
            {currentUser.role === 'bank' ? 'Контур андеррайтера (Служебный доступ)' : 'Личный кабинет предпринимателя'}
          </div>
        </div>
      </div>

      {/* Профиль вошедшего и Выход */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '13px', fontWeight: 700, color: '#0B1F35' }}>
            {currentUser.name}
          </div>
          <div style={{ fontSize: '11px', color: '#6F7985' }}>
            {currentUser.companyName || 'Сотрудник банка'}
          </div>
        </div>

        <div style={{
          width: '34px',
          height: '34px',
          borderRadius: '50%',
          backgroundColor: currentUser.role === 'bank' ? '#EF3124' : '#0B1F35',
          color: '#FFF',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '12px',
          fontWeight: 700,
        }}>
          {currentUser.avatarText}
        </div>

        <button
          onClick={onLogout}
          style={{
            marginLeft: '8px',
            backgroundColor: '#F3F4F7',
            border: 'none',
            padding: '8px 12px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: 600,
            color: '#5B6471',
            cursor: 'pointer',
          }}
        >
          Выйти
        </button>
      </div>
    </header>
  );
};
