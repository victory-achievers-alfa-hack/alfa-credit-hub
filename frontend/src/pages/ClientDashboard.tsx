import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { CreditApplication } from '../types/credit';
import { MOCK_PRODUCTS, MOCK_NEWS } from '../data/mockData';

interface ClientDashboardProps {
  applications: CreditApplication[];
}

export const ClientDashboard: React.FC<ClientDashboardProps> = ({ applications }) => {
  const navigate = useNavigate();
  const [selectedProduct, setSelectedProduct] = useState(MOCK_PRODUCTS[0]);
  const [calcAmount, setCalcAmount] = useState<number>(3000000);
  const [calcMonths, setCalcMonths] = useState<number>(12);

  // Статус бейдж хелпер
  const renderStatusBadge = (status: CreditApplication['status']) => {
    switch (status) {
      case 'APPROVED':
        return <span style={{ backgroundColor: '#E6F9ED', color: '#008744', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: 600 }}>✓ Одобрено</span>;
      case 'COUNTER_OFFER':
        return <span style={{ backgroundColor: '#FFF4E5', color: '#B76E00', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: 600 }}>⚡ Альтернативные условия</span>;
      case 'MANUAL_REVIEW':
        return <span style={{ backgroundColor: '#EDF5FF', color: '#0052CC', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: 600 }}>⏳ На рассмотрении</span>;
      case 'REJECTED':
        return <span style={{ backgroundColor: '#FDECEC', color: '#D9383A', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: 600 }}>✕ Отказ</span>;
      default:
        return <span style={{ backgroundColor: '#F0F1F3', color: '#5B6471', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: 600 }}>В обработке</span>;
    }
  };

  // Примерный расчет ежемесячного платежа
  const monthlyRate = selectedProduct.baseRate / 12 / 100;
  const estimatedMonthly = Math.round(
    (calcAmount * monthlyRate) / (1 - Math.pow(1 + monthlyRate, -calcMonths))
  );

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '32px 20px', display: 'flex', flexDirection: 'column', gap: '32px' }}>

      {/* Верхний баннер: Умный подбор кредита */}
      <section style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '16px',
        padding: '28px 32px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.03)',
        border: '1px solid #E9EBEF'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '6px', color: '#0B1F35' }}>
              Кредитование для вашего бизнеса
            </h1>
            <p style={{ color: '#6F7985', fontSize: '14px' }}>
              Подберите оптимальное финансирование за 2 минуты без визита в отделение
            </p>
          </div>
          <button
            onClick={() => navigate('/client/apply')}
            style={{
              backgroundColor: '#EF3124',
              color: '#FFFFFF',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '10px',
              fontWeight: 600,
              fontSize: '14px',
              boxShadow: '0 4px 12px rgba(239, 49, 36, 0.25)'
            }}
          >
            + Подать новую заявку
          </button>
        </div>

        {/* Сетка продуктов */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
          {MOCK_PRODUCTS.map((prod) => (
            <div
              key={prod.id}
              onClick={() => setSelectedProduct(prod)}
              style={{
                border: selectedProduct.id === prod.id ? '2px solid #EF3124' : '1px solid #E1E3E8',
                borderRadius: '12px',
                padding: '18px',
                cursor: 'pointer',
                backgroundColor: selectedProduct.id === prod.id ? '#FFF9F9' : '#FFFFFF',
                transition: 'all 0.2s'
              }}
            >
              <div style={{ fontSize: '15px', fontWeight: 700, marginBottom: '6px' }}>{prod.name}</div>
              <div style={{ color: '#EF3124', fontSize: '18px', fontWeight: 800, marginBottom: '8px' }}>
                от {prod.baseRate}%
              </div>
              <div style={{ fontSize: '12px', color: '#6F7985' }}>
                до {(prod.maxAmount / 1000000).toFixed(0)} млн ₽ на срок до {prod.maxTermMonths} мес.
              </div>
            </div>
          ))}
        </div>

        {/* Быстрый калькулятор */}
        <div style={{
          backgroundColor: '#F7F8FA',
          borderRadius: '12px',
          padding: '20px',
          display: 'grid',
          gridTemplateColumns: '1.2fr 1.2fr 1fr',
          gap: '24px',
          alignItems: 'center'
        }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
              <span>Сумма кредита:</span>
              <span style={{ color: '#EF3124' }}>{calcAmount.toLocaleString('ru-RU')} ₽</span>
            </div>
            <input
              type="range"
              min={selectedProduct.minAmount}
              max={selectedProduct.maxAmount}
              step={100000}
              value={calcAmount}
              onChange={(e) => setCalcAmount(Number(e.target.value))}
              style={{ width: '100%', accentColor: '#EF3124' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
              <span>Срок:</span>
              <span style={{ color: '#EF3124' }}>{calcMonths} мес.</span>
            </div>
            <input
              type="range"
              min={selectedProduct.minTermMonths}
              max={selectedProduct.maxTermMonths}
              step={1}
              value={calcMonths}
              onChange={(e) => setCalcMonths(Number(e.target.value))}
              style={{ width: '100%', accentColor: '#EF3124' }}
            />
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '12px', color: '#6F7985' }}>Примерный платеж:</div>
            <div style={{ fontSize: '20px', fontWeight: 800, color: '#0B1F35' }}>
              {estimatedMonthly.toLocaleString('ru-RU')} ₽/мес
            </div>
          </div>
        </div>
      </section>

      {/* Список существующих заявок предпринимателя */}
      <section style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '16px',
        padding: '28px 32px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.03)',
        border: '1px solid #E9EBEF'
      }}>
        <h2 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '18px' }}>
          История и статус обращений
        </h2>

        {applications.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#8A94A6' }}>
            У вас пока нет активных заявок. Выберите продукт и отправьте первую заявку!
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {applications.map((app) => (
              <div
                key={app.id}
                onClick={() => navigate(`/client/applications/${app.id}`)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '16px 20px',
                  borderRadius: '10px',
                  border: '1px solid #E9EBEF',
                  cursor: 'pointer',
                  transition: 'border 0.2s, background-color 0.2s',
                  backgroundColor: '#FFF'
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#FAFAFA')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#FFF')}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 700, fontSize: '15px' }}>{app.requestedProduct}</span>
                    <span style={{ fontSize: '12px', color: '#8A94A6' }}>№ {app.id} от {app.createdAt}</span>
                  </div>
                  <div style={{ fontSize: '13px', color: '#6F7985' }}>
                    Цель: {app.purpose}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 700, fontSize: '15px' }}>
                      {app.requestedAmount.toLocaleString('ru-RU')} ₽
                    </div>
                    <div style={{ fontSize: '12px', color: '#8A94A6' }}>на {app.requestedTermMonths} мес.</div>
                  </div>
                  <div>
                    {renderStatusBadge(app.status)}
                  </div>
                  <span style={{ color: '#8A94A6', fontSize: '18px' }}>›</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Отраслевая новостная лента под ОКВЭД клиента (То самое требование стр. 7 ТЗ!) */}
      <section style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '16px',
        padding: '24px 32px',
        border: '1px solid #E9EBEF'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 700 }}>
              Новости и спецпредложения для вашей отрасли
            </h3>
            <div style={{ fontSize: '12px', color: '#6F7985' }}>
              Персонализировано по ОКВЭД: 49.41 (Деятельность грузового автотранспорта)
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          {MOCK_NEWS.map((news) => (
            <div key={news.id} style={{
              padding: '16px',
              borderRadius: '10px',
              backgroundColor: '#F8F9FB',
              border: '1px solid #E4E6EB'
            }}>
              <span style={{
                backgroundColor: '#EF3124',
                color: '#FFF',
                fontSize: '10px',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '4px',
                textTransform: 'uppercase'
              }}>
                {news.tag}
              </span>
              <h4 style={{ fontSize: '14px', fontWeight: 600, margin: '8px 0 4px 0' }}>{news.title}</h4>
              <p style={{ fontSize: '12px', color: '#6F7985', lineHeight: '1.4' }}>{news.desc}</p>
            </div>
          ))}
        </div>
      </section>

    </div>
  );
};
