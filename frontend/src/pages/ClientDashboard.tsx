import { Button } from '@alfalab/core-components/button';
import { Typography } from '@alfalab/core-components/typography';
import { useNavigate } from 'react-router-dom';
import heroImage from '../assets/hero.png';
import { ApplicationStatusBadge } from '../components/ApplicationStatusBadge';
import { MetricCard } from '../components/MetricCard';
import { useAuth } from '../context/AutoContext';
import { useCredit } from '../context/CreditContext';
import { NEWS_ITEMS, PURPOSE_LABELS } from '../constants';
import { formatDateTime, formatMoney } from '../utils/format';

export function ClientDashboard() {
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const { getCompany, products, applications } = useCredit();
  const company = getCompany(currentUser?.companyId);

  if (!company) return null;

  const companyApplications = applications
    .filter((application) => application.companyId === company.id)
    .sort((first, second) => new Date(second.updatedAt).getTime() - new Date(first.updatedAt).getTime());
  const operatingFlow = company.monthlyRevenue - company.monthlyExpenses;
  const freeFlow = operatingFlow - company.existingPayments;

  return (
    <div className="page-shell">
      <section className="client-hero">
        <div className="client-hero__content">
          <div className="eyebrow eyebrow--light">Добрый день, {currentUser?.name.split(' ')[0]}</div>
          <Typography.Title tag="h1" view="xlarge" weight="bold" className="client-hero__title">
            Деньги на развитие — когда они нужны бизнесу
          </Typography.Title>
          <Typography.Text tag="p" view="primary-large" className="client-hero__text">
            Подберём продукт по оборотам компании и объясним каждый шаг решения.
          </Typography.Text>
          <div className="client-hero__actions">
            <Button view="accent" size={56} onClick={() => navigate('/client/financing')}>
              Подобрать финансирование
            </Button>
            <Button view="transparent" colors="inverted" size={56} onClick={() => navigate('/client/business')}>
              Посмотреть профиль
            </Button>
          </div>
        </div>
        <div className="client-hero__visual" aria-hidden="true">
          <div className="hero-orbit hero-orbit--one" />
          <div className="hero-orbit hero-orbit--two" />
          <img src={heroImage} alt="" />
          <div className="hero-amount">
            <small>Предварительный лимит</small>
            <strong>до 5 млн ₽</strong>
          </div>
        </div>
      </section>

      <section>
        <div className="section-heading">
          <div>
            <div className="eyebrow">Финансы компании</div>
            <Typography.Title tag="h2" view="medium" weight="bold">{company.name}</Typography.Title>
          </div>
          <button className="text-link" type="button" onClick={() => navigate('/client/business')}>Все данные →</button>
        </div>
        <div className="metrics-grid metrics-grid--four">
          <MetricCard label="Выручка в месяц" value={formatMoney(company.monthlyRevenue)} description="По данным расчётного счёта" icon="↗" />
          <MetricCard label="Операционные расходы" value={formatMoney(company.monthlyExpenses)} description="Без платежей по кредитам" icon="↘" />
          <MetricCard label="Текущие платежи" value={formatMoney(company.existingPayments)} description="Ежемесячная нагрузка" icon="≡" tone="warning" />
          <MetricCard label="Свободный поток" value={formatMoney(freeFlow)} description={`До долгов: ${formatMoney(operatingFlow)}`} icon="₽" tone={freeFlow > 0 ? 'positive' : 'warning'} />
        </div>
      </section>

      <section className="dashboard-grid">
        <article className="surface-card dashboard-applications">
          <div className="section-heading section-heading--compact">
            <div>
              <div className="eyebrow">Текущий процесс</div>
              <Typography.Title tag="h2" view="small" weight="bold">Мои заявки</Typography.Title>
            </div>
            <button className="text-link" type="button" onClick={() => navigate('/client/applications')}>Все заявки →</button>
          </div>

          {companyApplications.length === 0 ? (
            <div className="empty-state">
              <span className="empty-state__icon">＋</span>
              <strong>Заявок пока нет</strong>
              <p>Подберите продукт — реквизиты компании заполнятся автоматически.</p>
            </div>
          ) : (
            <div className="application-list">
              {companyApplications.slice(0, 3).map((application) => (
                <button
                  type="button"
                  className="application-row"
                  key={application.id}
                  onClick={() => navigate(`/client/applications/${application.id}`)}
                >
                  <span className="application-row__main">
                    <strong>{application.productName}</strong>
                    <small>{application.id} · {PURPOSE_LABELS[application.purpose]}</small>
                  </span>
                  <span className="application-row__amount">
                    <strong>{formatMoney(application.requestedAmount)}</strong>
                    <small>{formatDateTime(application.updatedAt)}</small>
                  </span>
                  <ApplicationStatusBadge status={application.status} compact />
                  <span className="application-row__chevron">›</span>
                </button>
              ))}
            </div>
          )}
        </article>

        <aside className="surface-card smart-summary">
          <div className="smart-summary__icon">AI</div>
          <div className="eyebrow">Финансовый помощник</div>
          <Typography.Title tag="h2" view="small" weight="bold">Что важно сейчас</Typography.Title>
          <p>После действующих платежей у бизнеса остаётся <b>{formatMoney(freeFlow)}</b> в месяц.</p>
          <div className="smart-summary__tip">
            Для комфортной нагрузки попробуйте срок 24–36 месяцев или меньшую сумму.
          </div>
          <Button view="secondary" size={48} block onClick={() => navigate('/client/financing')}>
            Рассчитать варианты
          </Button>
        </aside>
      </section>

      <section>
        <div className="section-heading">
          <div>
            <div className="eyebrow">Каталог</div>
            <Typography.Title tag="h2" view="medium" weight="bold">Решения для бизнеса</Typography.Title>
          </div>
        </div>
        <div className="product-preview-grid">
          {products.map((product) => (
            <button
              type="button"
              className={`product-preview product-preview--${product.accent}`}
              key={product.id}
              onClick={() => navigate('/client/financing')}
            >
              <span className="product-preview__index">0{products.indexOf(product) + 1}</span>
              <strong>{product.name}</strong>
              <p>{product.description}</p>
              <span>от {product.rate}% · до {formatMoney(product.maxAmount)}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="news-section">
        <div className="section-heading">
          <div>
            <div className="eyebrow">Полезное для вашей отрасли</div>
            <Typography.Title tag="h2" view="medium" weight="bold">Новости и возможности</Typography.Title>
          </div>
        </div>
        <div className="news-grid">
          {NEWS_ITEMS.map((item) => (
            <article className="news-card" key={item.id}>
              <span>{item.tag}</span>
              <strong>{item.title}</strong>
              <p>{item.description}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
