from decimal import Decimal, localcontext, ROUND_CEILING
import pytest
from test_financing import CITY, CAFE, PRODUCT, AT
from backend.src.scoring.stress import stress_summary
from backend.src.recommendation_contract import StressSummary


def summary(company=CAFE, product=PRODUCT, **changes):
    return stress_summary(company, product, **(dict(purpose='goods', amount=800000,
        term_months=24, evaluated_at=AT) | changes))


def test_city_screenshot_matches_independent_cashflow_and_annuity():
    result = summary(CITY, amount=200000, term_months=36)
    with localcontext() as context:
        context.prec = 50
        rate = Decimal('24') / 1200
        payment = (Decimal(200000) * rate / (1 - (1 + rate) ** -36)).quantize(Decimal('.01'), rounding=ROUND_CEILING)
        assert payment == Decimal('7846.58')
        denominator = Decimal(120000) + payment
        for decline, row in zip((0, 10, 20, 30), result['scenarios']):
            revenue = Decimal(900000) * (1 - Decimal(decline) / 100)
            flow = revenue - Decimal(740000)
            assert row['monthlyCashFlow'] == float(flow)
            assert row['coverage'] == pytest.approx(float(flow / denominator), abs=1e-12)
            assert row['operatingDeficit'] == float(max(Decimal(0), -flow))
            assert row['debtServiceShortfall'] == float(max(Decimal(0), denominator - flow))
    assert result['maxRevenueDeclinePercent'] == pytest.approx(0.021308333333333332)
    assert result['headroomStatus'] == 'negligible'
    assert '0,1%' in result['headroomMessage']
    assert result['scenarios'][2]['operatingDeficit'] == 20000
    assert result['scenarios'][3]['operatingDeficit'] == 110000
    assert all(row['monthlyRevenue'] >= 0 for row in result['scenarios'])
    assert result['scenarios'][2]['coverage'] < 0
    assert '20 000,00' in result['scenarios'][2]['coverageExplanation']


@pytest.mark.parametrize('revenue,expenses,status,percentage', [
    ('199.99','75','below_threshold',None),
    ('200','75','at_threshold',0),
    ('200.01','75','negligible',None),
    ('200.20','75','negligible',None),
    ('1000','874','positive',0.1),
])
def test_headroom_boundaries_are_not_collapsed_into_zero(revenue, expenses, status, percentage):
    company = CAFE | dict(monthlyRevenue=Decimal(revenue), monthlyExpenses=Decimal(expenses), existingPayments=0)
    product = PRODUCT | dict(minAmount=100, rate=0, terms=[1])
    result = summary(company, product, amount=100, term_months=1)
    assert result['headroomStatus'] == status
    if percentage is not None:
        assert result['maxRevenueDeclinePercent'] == percentage
    elif status == 'below_threshold':
        assert result['maxRevenueDeclinePercent'] is None
    else:
        assert 0 < result['maxRevenueDeclinePercent'] < 0.1
        assert '0,1%' in result['headroomMessage']


def test_zero_operating_cashflow_is_not_a_negative_revenue():
    result = summary(CAFE | dict(monthlyRevenue=100000, monthlyExpenses=100000), amount=100000)
    baseline = result['scenarios'][0]
    assert baseline['coverage'] == 0
    assert baseline['monthlyCashFlow'] == 0
    assert baseline['operatingDeficit'] == 0
    assert baseline['debtServiceShortfall'] > 0
    assert 'равна' in baseline['coverageExplanation']
    assert result['headroomStatus'] == 'below_threshold'


def test_new_fields_remain_optional_for_historical_stress_snapshots():
    current = summary()
    optional = {'baselineMonthlyRevenue', 'monthlyExpenses', 'existingMonthlyPayments', 'newMonthlyPayment',
                'coverageDefinition', 'headroomStatus', 'headroomMessage'}
    old = {key: value for key, value in current.items() if key not in optional}
    old['scenarios'] = [{key: value for key, value in row.items() if key not in {
        'monthlyCashFlow', 'operatingDeficit', 'debtServiceShortfall', 'coverageExplanation'}} for row in current['scenarios']]
    historical = StressSummary.model_validate(old)
    assert historical.headroomMessage is None
    assert historical.scenarios[0].operatingDeficit is None
