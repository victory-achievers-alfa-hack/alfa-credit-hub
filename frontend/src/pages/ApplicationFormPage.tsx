import { StressPanel } from '../components/StressPanel';
import { NextActions } from '../components/NextActions';
import { useEffect, useState } from 'react';
import { Button } from '@alfalab/core-components/button';
import { Checkbox } from '@alfalab/core-components/checkbox';
import { Typography } from '@alfalab/core-components/typography';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../context/AutoContext';
import { useCredit } from '../context/CreditContext';
import { PURPOSE_LABELS } from '../constants';
import type { CreditPurpose, Recommendation } from '../types/credit';
import { formatMoney } from '../utils/format';

const validPurposes: CreditPurpose[] = ['goods', 'equipment', 'cash_gap'];

export function ApplicationFormPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { currentUser } = useAuth();
  const { createApplication, recommend, getCompany, getProduct } = useCredit();
  const [confirmed, setConfirmed] = useState(false);
  const company = getCompany(currentUser?.companyId);
  const product = getProduct(searchParams.get('product') ?? '');
  const purposeParam = searchParams.get('purpose') as CreditPurpose;
  const purpose = validPurposes.includes(purposeParam) ? purposeParam : undefined;
  const amount = Number(searchParams.get('amount'));
  const termMonths = Number(searchParams.get('term'));

  const [recommendation, setRecommendation] = useState<Recommendation>();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const companyId = company?.id;
  const productId = product?.id;
  useEffect(() => {
    let active = true;
    // A changed URL requires a new server calculation and renewed confirmation.
    // oxlint-disable-next-line react/set-state-in-effect
    setLoading(true); setRecommendation(undefined); setConfirmed(false); setError('');
    if (!companyId || !productId || !purpose || !amount || !termMonths) { setLoading(false); return; }
    recommend({ companyId, purpose, amount, termMonths }).then(items => {
      if (active) setRecommendation(items.find(item => item.product.id === productId && item.amount === amount && item.termMonths === termMonths));
    }).catch(e => { if (active) setError(e instanceof Error ? e.message : 'Ошибка расчёта'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [companyId, productId, purpose, amount, termMonths, recommend]);
  if (loading) return <p role="status">Проверяем условия…</p>;
  if (error && !recommendation) return <div role="alert">{error}<Button onClick={() => navigate('/client/financing')}>К подбору</Button></div>;

  if (!company || !product || !purpose || !amount || !termMonths || !recommendation) {
    return (
      <div className="page-shell">
        <div className="surface-card empty-state empty-state--large">
          <span className="empty-state__icon">!</span>
          <strong>Не удалось восстановить условия заявки</strong>
          <p>Вернитесь к подбору и выберите кредитный продукт ещё раз.</p>
          <Button view="accent" size={48} onClick={() => navigate('/client/financing')}>К подбору</Button>
        </div>
      </div>
    );
  }

  const handleSubmit = async () => {
    if (submitting) return;
    setSubmitting(true); setError('');
    try {
    const application = await createApplication({
      companyId: company.id,
      productId: product.id,
      purpose,
      amount,
      termMonths,
    });
    navigate(`/client/applications/${application.id}`);
    } catch (e) { setError(e instanceof Error ? e.message : 'Не удалось отправить заявку'); }
    finally { setSubmitting(false); }
  };

  return (
    <div className="page-shell page-shell--narrow">
      <PageHeader
        eyebrow="Последний шаг"
        title="Проверьте заявку"
        description="Реквизиты и финансовые данные заполнены из профиля действующего клиента."
      />

      <div className="application-form-layout">
        <div className="application-form-main">
          <section className="surface-card form-review-section">
            <div className="review-section-heading">
              <span className="review-section-heading__number">01</span>
              <div>
                <Typography.Title tag="h2" view="small" weight="bold">Компания</Typography.Title>
                <p>Предзаполнено банком</p>
              </div>
              <span className="soft-tag soft-tag--positive">Проверено</span>
            </div>
            <dl className="detail-list detail-list--two-columns">
              <div><dt>Компания</dt><dd>{company.legalName}</dd></div>
              <div><dt>ИНН</dt><dd>{company.inn}</dd></div>
              <div><dt>Расчётный счёт</dt><dd>{company.account}</dd></div>
              <div><dt>Кредитная история</dt><dd>{company.hasOverdue ? 'Есть просрочки' : 'Без просрочек'}</dd></div>
            </dl>
          </section>

          <section className="surface-card form-review-section">
            <div className="review-section-heading">
              <span className="review-section-heading__number">02</span>
              <div>
                <Typography.Title tag="h2" view="small" weight="bold">Условия запроса</Typography.Title>
                <p>Выбранный кредитный продукт</p>
              </div>
              <button type="button" className="text-link" onClick={() => navigate('/client/financing')}>Изменить</button>
            </div>
            <div className="selected-product">
              <div className={`product-accent product-accent--${product.accent}`}>₽</div>
              <div className="selected-product__copy">
                <strong>{product.name}</strong>
                <span>{PURPOSE_LABELS[purpose]}</span>
              </div>
              <div className="selected-product__numbers">
                <div><small>Сумма</small><strong>{formatMoney(amount)}</strong></div>
                <div><small>Срок</small><strong>{termMonths} мес.</strong></div>
                <div><small>Ставка</small><strong>{recommendation.rate}%</strong></div>
                <div><small>Платёж</small><strong>{formatMoney(recommendation.monthlyPayment)}</strong></div>
              </div>
            </div>
            <NextActions actions={recommendation.actions} />
            <StressPanel stress={recommendation.stress} />
            {!recommendation.eligible && (
              <div className="explanation-box explanation-box--warning">
                <strong>Потребуется решение сотрудника банка</strong>
                <p>{recommendation.warning} Сотрудник банка проверит ограничения и может запросить сведения либо отказать.</p>
                {recommendation.recommendedAmount && <span>Расчётная комфортная сумма: <b>{formatMoney(recommendation.recommendedAmount)}</b></span>}
              </div>
            )}
          </section>
        </div>

        <aside className="surface-card submit-card">
          <div className="submit-card__icon">✓</div>
          <Typography.Title tag="h2" view="small" weight="bold">Всё готово</Typography.Title>
          <p>После отправки заявка появится у сотрудника банка. Статус можно отслеживать в кабинете.</p>
          <div className="submit-card__summary">
            <span><small>Запрашиваем</small><strong>{formatMoney(amount)}</strong></span>
            <span><small>Платёж</small><strong>{formatMoney(recommendation.monthlyPayment)}/мес.</strong></span>
          </div>
          {error && <p role="alert">{error}</p>}
          <Checkbox
            size={24}
            block
            checked={confirmed}
            onChange={(_, payload) => setConfirmed(payload.checked)}
            label="Подтверждаю корректность данных и согласен на демонстрационную обработку заявки"
          />
          <Button view="accent" size={56} block disabled={!confirmed || submitting || recommendation.group === 'unavailable'} onClick={handleSubmit}>
            Отправить заявку
          </Button>
          <small className="submit-card__legal">Это учебный сценарий. Реальная выдача денежных средств не выполняется.</small>
        </aside>
      </div>
    </div>
  );
}
