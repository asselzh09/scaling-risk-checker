import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import re

st.set_page_config(page_title="Ad Budget Planner", layout="centered")

# =========================
# Language
# =========================
lang = st.sidebar.selectbox("Language / Язык", ["English", "Русский"])
currency_symbol = st.sidebar.selectbox("Currency / Валюта", ["$", "₸", "₽", "฿", "€"])

T = {
    "English": {
        "title": "Ad Budget Planner",
        "subtitle": "See whether your current ad spend is healthy, too high, or safe to scale.",

        "biz_stage": "Choose your situation",
        "новый_бизнес": "New business",
        "existing_business": "Existing business",

        "mode": "Choose input mode",
        "m_manual": "Enter business numbers manually",
        "m_csv": "Upload Meta CSV/XLSX",
        "m_funnel": "Enter ad funnel manually",

        "rev": "Total revenue ($)",
        "cogs": "Total product cost / COGS ($)",
        "spend": "Current ad spend ($)",
        "orders": "Orders",
        "refund": "Refund rate (%)",

        "upload_meta": "Upload ad report",
        "upload_csv": "Upload CSV/XLSX",
        "upload_hint": "Upload a Meta CSV or XLSX report to auto-fill ad spend and conversations. Then enter average order value, product cost, and conversion rate.",
        "preview": "Preview",

        "camp_col": "Campaign name column",
        "spend_col": "Ad spend column",
        "results_col": "Results column",
        "indicator_col": "Result type column",
        "select_campaigns": "Select campaigns to include",

        "derived": "### Derived from CSV",
        "bridge": "Connect ad report to business numbers",

        "close_rate": "Conversation to order rate",
        "aov": "Average order value ($)",
        "cogs_po": "Product cost per order ($)",

        "manual_funnel_header": "Manual ad funnel inputs",
        "spend_f": "Ad spend ($)",
        "convos": "Messaging conversations",
        "clicks": "Clicks (optional)",
        "impr": "Impressions (optional)",

        "scale_header": "Scenario settings",
        "preset_label": "How does ad efficiency usually behave when you scale?",
        "preset_opt": "Optimistic",
        "preset_real": "Realistic",
        "preset_bad": "Pessimistic",
        "scale_inc": "Planned ad spend change (%)",
        "scale_decay": "If you double ad spend, how much can CAC increase (%)?",
        "note": "Example: if current CAC is $20 and this setting is 25%, then after doubling spend the model assumes CAC may rise to about $25.",

        "analyze": "Analyze",

        "no_msg_rows": "No messaging-specific rows were found in the selected result type column.",
        "msg_fallback_all": "No messaging-specific rows found. Using all selected rows instead.",
        "indicator_values": "Unique values from the selected result type column:",
        "conv_zero": "Conversations sum to 0. Can't continue.",
        "warn_orders": "Estimated orders are below 1. The app will use Orders = 1 to avoid division by zero.",
        "warn_convos": "Conversations must be greater than 0 to use this mode.",

        "status_hold": "🔴 HOLD — Current economics are weak or scaling leads to loss.",
        "status_fragile": "🟠 FRAGILE — Small CAC deterioration can break profitability.",
        "status_safe": "🟢 CONTROLLED — Unit economics can handle some growth.",

        "bottleneck_neg": "Your unit economics are negative even before ads.",
        "bottleneck_cac": "Customer acquisition cost is your main growth risk.",
        "bottleneck_ref": "Refunds are reducing profitability.",
        "bottleneck_margin": "Low margin limits safe scaling.",
        "bottleneck_ok": "No major structural problem detected.",

        "risk_hdr": "Risk meter",
        "baseline_hdr": "Current business snapshot",
        "unit_hdr": "Unit economics",
        "safe_cac_hdr": "Safe CAC",
        "max_budget_hdr": "Maximum safe ad budget",
        "real_analysis_hdr": "Real business analysis",
        "ads_effect_hdr": "Are ads helping or hurting?",
        "next_move_hdr": "Best next move",
        "main_constraint": "Main constraint",
        "rec_hdr": "Recommendation",
        "main_insight_hdr": "Main insight",
        "sim_hdr": "Selected scenario result",
        "safe_hdr": "Safe scaling limit",
        "safe_line": "Maximum safe ad spend increase before profit turns negative",
        "low_ceiling": "Low ceiling: aggressive scaling may quickly become unprofitable unless you improve margin, refunds, or CAC.",
        "table_hdr": "Scenario table",

        "chart_hdr": "Profit sensitivity curve",
        "chart_note": "This shows where reducing or increasing ad spend improves profit and where it starts hurting profit.",
        "current_point": "Current point",
        "peak_point": "Peak profit point",
        "breakeven_point": "Loss point",
        "peak_profit": "Peak profit",
        "peak_spend": "Best ad spend",
        "profit_cliff": "Profit cliff detected: beyond the peak, more spend reduces total profit.",

        "safe_cac": "Safe CAC",
        "current_cac": "Current CAC",
        "margin_buffer": "Margin buffer",

        "current_ad_spend": "Current ad spend",
        "max_safe_spend": "Maximum safe spend",
        "loss_point_spend": "Spend where profit turns negative",
        "profit_before_ads": "Profit before ads",
        "profit_after_ads": "Profit after ads",
        "ad_impact": "Ad cost impact",

        "forecast_spend": "Forecast spend",
        "forecast_cac": "Forecast CAC",
        "forecast_orders": "Forecast orders",
        "forecast_revenue": "Forecast revenue",
        "forecast_profit": "Forecast profit",

        "spend_increase_col": "Spend change %",
        "status_col": "Status",

        "newbiz_header": "New business planning",
        "planned_budget": "Planned ad budget ($)",
        "expected_cac": "Expected cost to get one customer ($)",
        "target_profit": "Target profit ($, optional)",
        "expected_orders": "Expected customers",
        "expected_revenue": "Expected revenue",
        "expected_profit": "Expected profit",
        "rec_budget": "Suggested test budget",
        "newbiz_result": "New business estimate",
        "newbiz_note": "Use this mode if you are planning your first ad budget and do not have real campaign data yet.",

        "example_btn": "Load example data",

        "reco_neg": "Your unit economics are negative before ads. Rework price, product cost, or refund rate first.",
        "reco_refund": "Refund rate is too high. Scaling ads now will amplify losses. Fix product quality, customer expectations, or support first.",
        "reco_margin": "Your margins are thin. Improve AOV or reduce product cost before pushing more spend.",
        "reco_cac_close": "Your current CAC is already too close to break-even. Scale carefully or improve conversion first.",
        "reco_good": "Healthy margin buffer. You still have room before CAC reaches break-even.",
        "reco_mid": "Economics look workable, but monitor CAC deterioration closely as you scale.",

        "insight_drop_pct": "If ad spend changes by {pct}%, profit may fall by {value}.",
        "insight_grow_pct": "If ad spend changes by {pct}%, profit may improve by {value}.",
        "insight_safe_limit": "Your business can safely increase ad spend by up to {pct}% before profit turns negative.",
        "insight_cac_ratio": "Your current CAC is already {pct}% of safe CAC.",

        "meta_diag": "Ad diagnostics (optional)",
        "cost_per_convo": "Cost per conversation",
        "conv_to_order": "Conversation to order rate",
        "estimated_cac": "Estimated CAC",
        "ctr": "Доля кликов",
        "cpc": "Стоимость клика",
        "click_to_convo": "Click to conversation rate",

        "ads_destroying": "Ads are currently destroying profitability.",
        "ads_ok": "Ads are still profitable at the current spend level.",
        "ads_weak": "Ads are still profitable, but efficiency is getting weak.",
        "ads_not_problem": "The core business economics are the main issue, not ad scaling.",
        "reduce_spend": "Reduce ad spend",
        "hold_spend": "Hold current spend",
        "scale_gradually": "Scale gradually",
        "fix_conversion": "Improve conversion before scaling",
        "fix_refunds": "Fix refund problem first",
        "fix_margin": "Improve margin first",
        "overspending_now": "Current spend appears above the profit peak.",
        "reducing_can_help": "Reducing ad spend may improve profit.",
        "current_close_to_peak": "Current spend is already close to the most profitable zone.",
        "still_room_to_scale": "There is still room to scale before profit peaks.",
    },
    "Русский": {
        "title": "Ad Budget Planner",
        "subtitle": "Помогает понять, не слишком ли много вы тратите на рекламу и можно ли безопасно увеличить бюджет.",

        "biz_stage": "Выберите вашу ситуацию",
        "новый_бизнес": "Новый бизнес",
        "existing_business": "Есть действующий бизнес",

        "mode": "Выберите способ ввода",
        "m_manual": "Ввести цифры бизнеса вручную",
        "m_csv": "Загрузить рекламный отчёт",
        "m_funnel": "Ввести рекламную воронку вручную",

        "rev": "Общая выручка ($)",
        "cogs": "Общая себестоимость / COGS ($)",
        "spend": "Текущий расход на рекламу ($)",
        "orders": "Заказы",
        "refund": "Процент возвратов (%)",

        "upload_meta": "Загрузить рекламный отчёт",
        "upload_csv": "Загрузить файл отчёта",
        "upload_hint": "Загрузите рекламный отчёт, чтобы автоматически подтянуть расходы и количество обращений. Затем введите средний чек, себестоимость и конверсию в покупку.",
        "preview": "Превью",

        "camp_col": "Колонка с названием кампании",
        "spend_col": "Колонка с расходом на рекламу",
        "results_col": "Колонка с результатами",
        "indicator_col": "Колонка с типом результата",
        "select_campaigns": "Выберите рекламные кампании",

        "derived": "### Получено из файла",
        "bridge": "Свяжите рекламный отчёт с бизнес-цифрами",

        "close_rate": "Конверсия в покупку",
        "aov": "Средний чек ($)",
        "cogs_po": "Себестоимость одного заказа ($)",

        "manual_funnel_header": "Ручной ввод данных по рекламе",
        "spend_f": "Расход на рекламу ($)",
        "convos": "Диалоги",
        "clicks": "Клики (опционально)",
        "impr": "Показы (опционально)",

        "scale_header": "Настройки расчёта",
        "preset_label": "Как обычно ведёт себя реклама, когда вы увеличиваете бюджет?",
        "preset_opt": "Лучший вариант",
        "preset_real": "Средний вариант",
        "preset_bad": "Худший вариант",
        "scale_inc": "На сколько хотите изменить рекламный бюджет (%)",
        "scale_decay": "Если увеличить бюджет в 2 раза, на сколько может вырасти стоимость привлечения клиента (%)?",
        "note": "Пример: если сейчас привлечение одного клиента стоит 20, а здесь стоит 25%, то при удвоении бюджета модель предполагает рост этой стоимости примерно до 25.",

        "analyze": "Рассчитать",

        "no_msg_rows": "В выбранной колонке типа результата не найдено строк, связанных с сообщениями.",
        "msg_fallback_all": "Строки с сообщениями не найдены. Используются все выбранные строки.",
        "indicator_values": "Уникальные значения в выбранной колонке типа результата:",
        "conv_zero": "Количество обращений = 0. Невозможно продолжить расчёт.",
        "warn_orders": "Расчётные заказы меньше 1. Приложение использует Orders = 1, чтобы избежать деления на ноль.",
        "warn_convos": "Количество обращений должно быть больше 0 для этого режима.",

        "status_hold": "🔴 СТОП — Сейчас экономика слабая или рост бюджета ведёт к убытку.",
        "status_fragile": "🟠 ОСТОРОЖНО — Даже небольшое ухудшение может сильно снизить прибыль.",
        "status_safe": "🟢 НОРМАЛЬНО — Экономика выдерживает некоторый рост.",

        "bottleneck_neg": "Экономика отрицательная ещё до рекламы.",
        "bottleneck_cac": "Главный риск сейчас — слишком дорогой клиент.",
        "bottleneck_ref": "Возвраты съедают прибыль.",
        "bottleneck_margin": "Низкая маржа ограничивает безопасный рост.",
        "bottleneck_ok": "Серьёзных проблем не видно.",

        "risk_hdr": "Уровень риска",
        "baseline_hdr": "Текущая ситуация",
        "unit_hdr": "Экономика заказа",
        "safe_cac_hdr": "Безопасная стоимость клиента",
        "max_budget_hdr": "Максимально безопасный бюджет на рекламу",
        "real_analysis_hdr": "Разбор текущих цифр",
        "ads_effect_hdr": "Реклама сейчас помогает или мешает?",
        "next_move_hdr": "Что делать дальше",
        "main_constraint": "Главная проблема",
        "rec_hdr": "Рекомендация",
        "main_insight_hdr": "Главный итог",
        "sim_hdr": "Результат выбранного прогноза",
        "safe_hdr": "Предел безопасного увеличения бюджета",
        "safe_line": "Насколько можно увеличить бюджет, прежде чем прибыль уйдёт в минус",
        "low_ceiling": "Запас небольшой: если резко увеличивать бюджет, можно быстро уйти в минус.",
        "table_hdr": "Таблица сценариев",

        "chart_hdr": "Как меняется прибыль при изменении бюджета",
        "chart_note": "Показывает, где изменение бюджета помогает прибыли, а где уже начинает вредить.",
        "current_point": "Текущая точка",
        "peak_point": "Лучшая точка по прибыли",
        "breakeven_point": "Точка ухода в убыток",
        "peak_profit": "Лучшая прибыль",
        "peak_spend": "Лучший бюджет на рекламу",
        "profit_cliff": "После определённой точки дальнейший рост бюджета снижает общую прибыль.",

        "safe_cac": "Безопасная стоимость клиента",
        "current_cac": "Текущая стоимость клиента",
        "margin_buffer": "Запас прибыли с заказа",

        "current_ad_spend": "Текущий бюджет на рекламу",
        "max_safe_spend": "Максимально безопасный бюджет",
        "loss_point_spend": "Бюджет, при котором прибыль уходит в минус",
        "profit_before_ads": "Прибыль до рекламы",
        "profit_after_ads": "Прибыль после рекламы",
        "ad_impact": "Влияние рекламы на прибыль",

        "forecast_spend": "Расходы в расчёте",
        "forecast_cac": "Стоимость клиента в расчёте",
        "forecast_orders": "Заказы в расчёте",
        "forecast_revenue": "Выручка в расчёте",
        "forecast_profit": "Прибыль в расчёте",

        "spend_increase_col": "Изменение бюджета, %",
        "status_col": "Статус",

        "newbiz_header": "План для нового бизнеса",
        "planned_budget": "Планируемый бюджет на рекламу",
        "expected_cac": "Ожидаемая стоимость одного клиента",
        "target_profit": "Желаемая прибыль (необязательно)",
        "expected_orders": "Ожидаемое число клиентов",
        "expected_revenue": "Ожидаемая выручка",
        "expected_profit": "Ожидаемая прибыль",
        "rec_budget": "Рекомендуемый бюджет на тест",
        "newbiz_result": "Предварительный расчёт для нового бизнеса",
        "newbiz_note": "Используйте этот режим, если вы только планируете первый запуск рекламы и у вас ещё нет реальных цифр.",

        "example_btn": "Подставить пример",

        "reco_neg": "Экономика отрицательная ещё до рекламы. Сначала пересоберите цену, себестоимость или уровень возвратов.",
        "reco_refund": "Процент возвратов слишком высокий. Масштабирование рекламы усилит убытки. Сначала исправьте качество продукта, ожидания клиента или поддержку.",
        "reco_margin": "Прибыль с заказа слишком маленькая. Лучше повысить средний чек или снизить себестоимость перед ростом бюджета.",
        "reco_cac_close": "Стоимость клиента уже слишком близка к опасной границе. Лучше расти осторожно или сначала улучшить продажи.",
        "reco_good": "Хороший запас маржи. У вас ещё есть пространство до точки безубыточности по стоимости привлечения клиента.",
        "reco_mid": "Цифры пока выглядят рабочими, но при росте бюджета следите, не дорожает ли клиент.",

        "insight_drop_pct": "Если изменить рекламный бюджет на {pct}%, прибыль может снизиться на {value}.",
        "insight_grow_pct": "Если изменить рекламный бюджет на {pct}%, прибыль может вырасти на {value}.",
        "insight_safe_limit": "Ваш бизнес может безопасно увеличить рекламный бюджет максимум на {pct}%, прежде чем прибыль станет отрицательной.",
        "insight_cac_ratio": "Текущая стоимость клиента уже составляет {pct}% от безопасного уровня.",

        "meta_diag": "Дополнительные показатели рекламы",
        "cost_per_convo": "Стоимость диалога",
        "conv_to_order": "Конверсия в покупку",
        "estimated_cac": "Расчётная стоимость клиента",
        "ctr": "Доля кликов",
        "cpc": "Стоимость клика",
        "click_to_convo": "Конверсия из клика в обращение",

        "ads_destroying": "Сейчас реклама уводит бизнес в минус.",
        "ads_ok": "Сейчас реклама ещё приносит прибыль.",
        "ads_weak": "Реклама пока приносит прибыль, но уже слабеет.",
        "ads_not_problem": "Главная проблема сейчас не в рекламе, а в самой экономике бизнеса.",
        "reduce_spend": "Снизить бюджет на рекламу",
        "hold_spend": "Оставить текущий бюджет",
        "scale_gradually": "Увеличивать бюджет постепенно",
        "fix_conversion": "Сначала улучшить продажи",
        "fix_refunds": "Сначала решить проблему возвратов",
        "fix_margin": "Сначала увеличить прибыль с заказа",
        "overspending_now": "Текущий бюджет на рекламу, похоже, выше точки максимальной прибыли.",
        "reducing_can_help": "Снижение бюджета может увеличить прибыль.",
        "current_close_to_peak": "Текущий бюджет уже близок к лучшей зоне по прибыли.",
        "still_room_to_scale": "До лучшей точки по прибыли у вас ещё есть запас для роста.",
    },
}
t = T[lang]

# =========================
# Style
# =========================
st.markdown(
    """
    <style>
    .big-status {
        font-size: 22px;
        font-weight: 700;
        padding: 14px 18px;
        border-radius: 10px;
        margin-top: 8px;
        margin-bottom: 12px;
        border-left: 5px solid;
    }
    .safe  { border-color: #2e9e5b; color: #2e9e5b; background: rgba(46,158,91,0.10); }
    .fragile { border-color: #d4882a; color: #d4882a; background: rgba(212,136,42,0.10); }
    .hold  { border-color: #d44242; color: #d44242; background: rgba(212,66,66,0.10); }
    .small-note { opacity: 0.6; font-size: 13px; }
    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,0.2);
        padding: 10px 12px;
        border-radius: 10px;
    }
    /* Progress tab hint */
    .tab-hint {
        font-size: 13px;
        opacity: 0.55;
        margin-bottom: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title(t["title"])
st.write(t["subtitle"])


# =========================
# Helpers
# =========================
def safe_div(a, b):
    return a / b if b not in [0, 0.0, None] else 0.0


def format_money(v):
    if v is None:
        return "n/a"
    try:
        return f"{currency_symbol}{float(v):,.2f}"
    except (TypeError, ValueError):
        return "n/a"




def money_label(label: str) -> str:
    return label.replace("($)", f"({currency_symbol})")

def parse_number_series(series):
    def parse_one(value):
        if pd.isna(value):
            return None

        s = str(value).strip()
        if not s:
            return None

        s = re.sub(r"[^\d,.\-]", "", s)
        if not s or s in {"-", ".", ",", "-.", "-,"}:
            return None

        if "," in s and "." in s:
            if s.rfind(",") > s.rfind("."):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s:
            whole, frac = s.rsplit(",", 1)
            if frac.isdigit() and len(frac) in (1, 2):
                s = whole.replace(".", "") + "." + frac
            else:
                s = s.replace(",", "")

        try:
            return float(s)
        except ValueError:
            return None

    return series.apply(parse_one).fillna(0.0)


def read_uploaded_report(uploaded_file):
    name = (getattr(uploaded_file, "name", "") or "").lower()

    if name.endswith(".xlsx") or name.endswith(".xls"):
        uploaded_file.seek(0)
        return pd.read_excel(uploaded_file)

    uploaded_file.seek(0)
    raw_bytes = uploaded_file.getvalue()

    best_df = None
    best_score = (-1, -1)

    for enc in ["utf-8", "utf-8-sig", "utf-16", "latin1", "cp1252"]:
        try:
            text = raw_bytes.decode(enc)
        except UnicodeDecodeError:
            continue

        for sep in [None, ",", ";", "\t", "|"]:
            try:
                df = pd.read_csv(
                    io.StringIO(text),
                    encoding=enc,
                    sep=sep,
                    engine="python",
                    on_bad_lines="skip",
                )
            except Exception:
                continue

            df.columns = [str(c).strip().lstrip("\ufeff") for c in df.columns]
            score = (
                len(df.columns),
                sum(not str(c).lower().startswith("unnamed") for c in df.columns),
            )

            if score > best_score:
                best_df = df
                best_score = score

        if best_df is not None and best_score[0] > 1:
            return best_df

    if best_df is not None:
        return best_df

    uploaded_file.seek(0)
    try:
        return pd.read_csv(
            uploaded_file,
            encoding="latin1",
            sep=None,
            engine="python",
            on_bad_lines="skip",
        )
    except Exception:
        uploaded_file.seek(0)
        return pd.read_csv(
            uploaded_file,
            encoding="latin1",
            engine="python",
            on_bad_lines="skip",
        )


def guess_index_from_patterns(cols, patterns):
    normalized_cols = [re.sub(r"[^a-z0-9]+", " ", str(c).lower()).strip() for c in cols]

    for pattern in patterns:
        if pattern in cols:
            return cols.index(pattern)

    for pattern in patterns:
        pattern_norm = re.sub(r"[^a-z0-9]+", " ", pattern.lower()).strip()
        for idx, col_norm in enumerate(normalized_cols):
            if pattern_norm and pattern_norm in col_norm:
                return idx

    return 0


def get_data_quality_note(meta_convos, ad_spend, close_rate, aov):
    if ad_spend <= 0:
        return "No ad spend detected." if lang == "English" else "Не обнаружены расходы на рекламу."
    if meta_convos <= 0:
        return "No conversations detected from the selected report/columns." if lang == "English" else "В выбранном отчёте и колонках не обнаружены диалоги."
    if meta_convos < 10:
        return "Very low conversation volume. Treat results as directional only." if lang == "English" else "Очень мало диалогов. Считайте результат только ориентиром."
    if close_rate <= 0 or aov <= 0:
        return "Business assumptions are incomplete. Results are only partial." if lang == "English" else "Бизнес-предпосылки заполнены не полностью. Результаты будут частичными."
    return None


def is_projection_only(meta_convos):
    return meta_convos < 10


def simulate_scale(
    revenue: float,
    cogs: float,
    ad_spend: float,
    orders: float,
    refund_rate_pct: float,
    spend_change_pct: float,
    cac_deterioration_per_100_pct: float,
):
    revenue = float(revenue or 0.0)
    cogs = float(cogs or 0.0)
    ad_spend = float(ad_spend or 0.0)
    orders = float(orders or 0.0)
    rr = float(refund_rate_pct or 0.0) / 100.0
    g = float(spend_change_pct or 0.0) / 100.0
    k = float(cac_deterioration_per_100_pct or 0.0) / 100.0

    if orders <= 0:
        orders = 1.0

    aov = safe_div(revenue, orders)
    cogs_per_order = safe_div(cogs, orders)
    cac = safe_div(ad_spend, orders)
    refund_cost_per_order = aov * rr

    contribution_margin = aov - cogs_per_order - refund_cost_per_order
    gross_margin_pct = safe_div((revenue - cogs), revenue) * 100 if revenue > 0 else 0.0

    baseline_refund_cost = revenue * rr
    profit_before_ads = revenue - cogs - baseline_refund_cost
    baseline_profit = profit_before_ads - ad_spend
    ad_impact = profit_before_ads - baseline_profit  # equals ad_spend

    break_even_cac = contribution_margin
    risk_ratio = safe_div(cac, break_even_cac) if break_even_cac > 0 else 999.0
    margin_buffer = break_even_cac - cac

    new_spend = ad_spend * (1 + g)
    if new_spend < 0:
        new_spend = 0.0

    if cac <= 0:
        new_cac = 0.0
        new_orders = orders
    else:
        # growth hurts CAC, reduction improves CAC symmetrically
        new_cac = cac * (1 + k * g)
        if new_cac < 0:
            new_cac = 0.0
        new_orders = safe_div(new_spend, new_cac) if new_cac > 0 else 0.0

    new_revenue = aov * new_orders
    new_cogs = cogs_per_order * new_orders
    new_refund_cost = new_revenue * rr
    new_profit_before_ads = new_revenue - new_cogs - new_refund_cost
    new_profit = new_profit_before_ads - new_spend
    new_risk_ratio = safe_div(new_cac, break_even_cac) if break_even_cac > 0 else 999.0

    return {
        "AOV": aov,
        "cogs_per_order": cogs_per_order,
        "cac": cac,
        "break_even_cac": break_even_cac,
        "gross_margin_pct": gross_margin_pct,
        "contribution_margin": contribution_margin,
        "baseline_profit": baseline_profit,
        "profit_before_ads": profit_before_ads,
        "ad_impact": ad_impact,
        "baseline_refund_cost": baseline_refund_cost,
        "risk_ratio": risk_ratio,
        "margin_buffer": margin_buffer,
        "new_spend": new_spend,
        "new_cac": new_cac,
        "new_orders": new_orders,
        "new_revenue": new_revenue,
        "new_cogs": new_cogs,
        "new_refund_cost": new_refund_cost,
        "new_profit_before_ads": new_profit_before_ads,
        "new_profit": new_profit,
        "new_risk_ratio": new_risk_ratio,
    }


def get_status(res):
    if res["baseline_profit"] < 0 or res["break_even_cac"] <= 0 or res["new_profit"] < 0:
        return t["status_hold"], "hold"
    if res["new_risk_ratio"] > 0.80:
        return t["status_fragile"], "fragile"
    return t["status_safe"], "safe"


def get_bottleneck(aov, cogs_per_order, cac, break_even_cac, refund_rate):
    if break_even_cac <= 0:
        return t["bottleneck_neg"]
    if cac > break_even_cac:
        return t["bottleneck_cac"]
    if refund_rate > 10:
        return t["bottleneck_ref"]
    if aov > 0 and ((aov - cogs_per_order) / aov) < 0.35:
        return t["bottleneck_margin"]
    return t["bottleneck_ok"]


def get_recommendation(res, refund_rate):
    aov = res["AOV"]
    cogs_per_order = res["cogs_per_order"]
    cac = res["cac"]
    break_even_cac = res["break_even_cac"]

    if break_even_cac <= 0:
        return t["reco_neg"]
    if refund_rate >= 15:
        return t["reco_refund"]
    if aov > 0 and (cogs_per_order / aov) > 0.50:
        return t["reco_margin"]
    if break_even_cac > 0 and cac >= break_even_cac * 0.80:
        return t["reco_cac_close"]
    if break_even_cac > 0 and cac < break_even_cac * 0.50:
        return t["reco_good"]
    return t["reco_mid"]


def find_safe_max_scale_pct(
    revenue: float,
    cogs: float,
    ad_spend: float,
    orders: float,
    refund_rate_pct: float,
    cac_deterioration_per_100_pct: float,
    max_search_pct: int = 300,
):
    # Check baseline first
    baseline = simulate_scale(
        revenue=revenue, cogs=cogs, ad_spend=ad_spend, orders=orders,
        refund_rate_pct=refund_rate_pct, spend_change_pct=0,
        cac_deterioration_per_100_pct=cac_deterioration_per_100_pct,
    )
    if baseline["new_profit"] < 0:
        return 0
    last_safe = 0
    for pct in range(1, max_search_pct + 1):
        r = simulate_scale(
            revenue=revenue, cogs=cogs, ad_spend=ad_spend, orders=orders,
            refund_rate_pct=refund_rate_pct, spend_change_pct=pct,
            cac_deterioration_per_100_pct=cac_deterioration_per_100_pct,
        )
        if r["new_profit"] >= 0:
            last_safe = pct
        else:
            break
    return last_safe


def find_loss_point_spend(
    revenue: float,
    cogs: float,
    ad_spend: float,
    orders: float,
    refund_rate_pct: float,
    cac_deterioration_per_100_pct: float,
    max_search_pct: int = 300,
):
    for pct in range(0, max_search_pct + 1):
        r = simulate_scale(
            revenue=revenue,
            cogs=cogs,
            ad_spend=ad_spend,
            orders=orders,
            refund_rate_pct=refund_rate_pct,
            spend_change_pct=pct,
            cac_deterioration_per_100_pct=cac_deterioration_per_100_pct,
        )
        if r["new_profit"] < 0:
            return r["new_spend"]
    return None


def build_profit_curve(
    revenue: float,
    cogs: float,
    ad_spend: float,
    orders: float,
    refund_rate_pct: float,
    cac_deterioration_per_100_pct: float,
    min_scale_pct: int = -80,
    max_scale_pct: int = 300,
):
    points = []
    for pct in range(min_scale_pct, max_scale_pct + 1, 10):
        r = simulate_scale(
            revenue=revenue,
            cogs=cogs,
            ad_spend=ad_spend,
            orders=orders,
            refund_rate_pct=refund_rate_pct,
            spend_change_pct=pct,
            cac_deterioration_per_100_pct=cac_deterioration_per_100_pct,
        )
        points.append(
            {
                "scale_pct": pct,
                "ad_spend": r["new_spend"],
                "profit": r["new_profit"],
            }
        )
    return pd.DataFrame(points)


def plot_profit_curve(df_curve):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(df_curve["ad_spend"], df_curve["profit"], marker="o")
    ax.axhline(0, linewidth=1)

    current_row = df_curve[df_curve["scale_pct"] == 0]
    current = current_row.iloc[0] if not current_row.empty else df_curve.iloc[0]
    peak_idx = df_curve["profit"].idxmax()
    peak = df_curve.loc[peak_idx]

    ax.scatter([current["ad_spend"]], [current["profit"]], s=60)
    ax.annotate(
        t["current_point"],
        (current["ad_spend"], current["profit"]),
        textcoords="offset points",
        xytext=(8, 8),
    )

    ax.scatter([peak["ad_spend"]], [peak["profit"]], s=60)
    ax.annotate(
        t["peak_point"],
        (peak["ad_spend"], peak["profit"]),
        textcoords="offset points",
        xytext=(8, -16),
    )

    breakeven_rows = df_curve[df_curve["profit"] <= 0]
    if len(breakeven_rows) > 0:
        be = breakeven_rows.iloc[0]
        ax.scatter([be["ad_spend"]], [be["profit"]], s=60)
        ax.annotate(
            t["breakeven_point"],
            (be["ad_spend"], be["profit"]),
            textcoords="offset points",
            xytext=(8, 8),
        )

    ax.set_xlabel("Ad Spend")
    ax.set_ylabel("Net Profit")
    ax.set_title(t["chart_hdr"])
    st.pyplot(fig)
    plt.close(fig)

    peak_profit = float(peak["profit"])
    peak_spend = float(peak["ad_spend"])
    cliff_detected = False
    if peak_idx < len(df_curve) - 1:
        final_profit = float(df_curve.iloc[-1]["profit"])
        cliff_detected = final_profit < peak_profit

    return peak_profit, peak_spend, cliff_detected


def profit_flag(p, baseline_revenue):
    if p < 0:
        return "🔴"
    if baseline_revenue > 0 and p < baseline_revenue * 0.05:
        return "🟠"
    return "🟢"


def get_ads_verdict(res):
    if res["baseline_profit"] < 0 and res["profit_before_ads"] > 0:
        return t["ads_destroying"]
    if res["baseline_profit"] > 0 and res["margin_buffer"] > 0 and res["risk_ratio"] < 0.7:
        return t["ads_ok"]
    if res["baseline_profit"] > 0 and res["margin_buffer"] > 0:
        return t["ads_weak"]
    return t["ads_not_problem"]


def get_best_next_move(res, refund_rate, peak_spend, current_spend):
    aov = res["AOV"]
    cogs_per_order = res["cogs_per_order"]

    if refund_rate >= 15:
        return t["fix_refunds"]
    if aov > 0 and (cogs_per_order / aov) > 0.50:
        return t["fix_margin"]
    if res["baseline_profit"] < 0 and res["profit_before_ads"] > 0:
        return t["reduce_spend"]
    if current_spend > peak_spend * 1.05:
        return t["reduce_spend"]
    if res["risk_ratio"] >= 0.80:
        return t["fix_conversion"]
    if res["risk_ratio"] < 0.55 and current_spend < peak_spend * 0.95:
        return t["scale_gradually"]
    return t["hold_spend"]


def tr(en, ru):
    return en if lang == "English" else ru


def classify_mode_v2(source_key, used_conversations, real_orders, threshold, close_rate_confidence, close_rate_source, has_economics, true_spend):
    if source_key == "новый_бизнес_assumptions_only":
        return "new_business"
    # Require close_rate_source to be real_data or past_campaigns (not guess),
    # and close_rate_confidence to not be low. This aligns with get_confidence_v2's
    # high-confidence gate so the badge and the confidence label never contradict each other.
    close_rate_ok = close_rate_confidence != "low" and close_rate_source != "guess"
    if (
        used_conversations >= threshold
        and real_orders >= 3
        and has_economics
        and true_spend > 0
        and close_rate_ok
    ):
        return "validated"
    return "early_test"


def is_low_confidence_v2(source_key, mode_key, real_orders, close_rate_source, used_conversations, threshold):
    return (
        source_key == "новый_бизнес_assumptions_only"
        or mode_key == "ранний_тест"
        or real_orders <= 0
        or close_rate_source == "guess"
        or used_conversations < threshold
    )


def get_confidence_v2(source_key, used_conversations, real_orders, threshold, close_rate_source, spend_is_adjusted, has_economics, lead_quality):
    reasons = []

    if source_key == "новый_бизнес_assumptions_only":
        reasons.append(tr("assumptions only", "только предположения"))
    if used_conversations < threshold:
        reasons.append(tr("low conversation volume", "мало диалогов"))
    if real_orders <= 0 and source_key != "новый_бизнес_assumptions_only":
        reasons.append(tr("no real orders yet", "ещё нет реальных заказов"))
    if close_rate_source == "guess":
        reasons.append(tr("close rate is guessed", "конверсия в покупку указана как предположение"))
    if not has_economics:
        reasons.append(tr("economics incomplete", "экономика заполнена не полностью"))
    if spend_is_adjusted:
        reasons.append(tr("spend adjusted manually", "расход скорректирован вручную"))
    if lead_quality == "weak":
        reasons.append(tr("качество обращений слабое", "качество обращений слабое"))

    if source_key == "новый_бизнес_assumptions_only":
        return tr("Low", "Низкая"), reasons
    if (
        used_conversations >= threshold
        and real_orders >= 3
        and close_rate_source == "real_data"
        and has_economics
        and not spend_is_adjusted
        and lead_quality != "weak"
    ):
        return tr("High", "Высокая"), reasons or [tr("real orders and solid downstream data", "есть реальные заказы и достаточно данных")]
    return tr("Medium", "Средняя"), reasons


def get_recommendation_v2(
    mode_key,
    true_spend,
    reported_spend,
    used_conversations,
    qualified_leads,
    real_orders,
    refund_count,
    lead_quality,
    break_even_cac,
    target_cac,
    cost_per_conversation,
    estimated_cac,
    real_cac,
    max_cost_per_conversation,
    recommended_test_budget,
    target_conversations,
    close_rate_source,
):
    if mode_key == "новый_бизнес":
        headline = tr("Scenario planning only", "Только предварительный расчёт")
        body = [
            tr("Use this as a validation plan, not a profit promise.", "Используйте это как план проверки, а не как обещание прибыли."),
            tr(f"Target CAC: {format_money(max(target_cac, 0.0))}", f"Целевая стоимость привлечения клиента: {format_money(max(target_cac, 0.0))}"),
            tr(
                f"Бюджет на тест for {int(target_conversations)} conversations: {format_money(recommended_test_budget)}",
                f"Бюджет на проверку для {int(target_conversations)} обращений: {format_money(recommended_test_budget)}",
            ),
        ]
        return headline, body

    if mode_key == "ранний_тест":
        headline = tr("Early test: collect more evidence", "Ранний тест: соберите больше данных")
        track_metric = (
            tr("actual paid spend and real conversations", "фактически оплаченный расход и реальные диалоги")
            if real_orders <= 0
            else tr("qualified leads, first orders, and refunds", "квалифицированные обращения, первые заказы и возвраты")
        )
        if max_cost_per_conversation > 0 and cost_per_conversation > max_cost_per_conversation * 1.15:
            body = [
                tr(f"Current cost per conversation: {format_money(cost_per_conversation)}", f"Текущая стоимость обращения: {format_money(cost_per_conversation)}"),
                tr(f"Target max cost per conversation: {format_money(max_cost_per_conversation)}", f"Целевая максимальная стоимость обращения: {format_money(max_cost_per_conversation)}"),
                tr(
                    f"Budget to reach {int(target_conversations)} conversations: {format_money(recommended_test_budget)}",
                    f"Бюджет, чтобы дойти до {int(target_conversations)} обращений: {format_money(recommended_test_budget)}",
                ),
                tr(f"Current signal looks expensive for testing. Track {track_metric} next.", f"Текущий сигнал выглядит дорогим даже для теста. Дальше отслеживайте {track_metric}."),
            ]
        elif max_cost_per_conversation > 0 and cost_per_conversation > max_cost_per_conversation:
            body = [
                tr(f"Current cost per conversation: {format_money(cost_per_conversation)}", f"Текущая стоимость обращения: {format_money(cost_per_conversation)}"),
                tr(f"Target max cost per conversation: {format_money(max_cost_per_conversation)}", f"Целевая максимальная стоимость обращения: {format_money(max_cost_per_conversation)}"),
                tr(
                    f"Budget to reach {int(target_conversations)} conversations: {format_money(recommended_test_budget)}",
                    f"Бюджет, чтобы дойти до {int(target_conversations)} обращений: {format_money(recommended_test_budget)}",
                ),
                tr(f"Current signal is borderline. Collect more evidence carefully and track {track_metric} next.", f"Текущие цифры пограничные. Аккуратно соберите больше данных и дальше отслеживайте {track_metric}."),
            ]
        else:
            body = [
                tr(f"Current cost per conversation: {format_money(cost_per_conversation)}", f"Текущая стоимость обращения: {format_money(cost_per_conversation)}"),
                tr(f"Target max cost per conversation: {format_money(max_cost_per_conversation)}", f"Целевая максимальная стоимость обращения: {format_money(max_cost_per_conversation)}"),
                tr(
                    f"Budget to reach {int(target_conversations)} conversations: {format_money(recommended_test_budget)}",
                    f"Бюджет, чтобы дойти до {int(target_conversations)} обращений: {format_money(recommended_test_budget)}",
                ),
                tr(f"The current signal may be workable, but there is not enough evidence yet. Track {track_metric} next.", f"Текущие цифры могут быть рабочими, но данных пока недостаточно. Дальше отслеживайте {track_metric}."),
            ]
        return headline, body

    if refund_count > 0:
        return tr("Fix refunds first", "Сначала разберитесь с возвратами"), [
            tr("Refund leakage is reducing how much CAC the business can safely afford.", "Возвраты уменьшают CAC, который бизнес может безопасно выдерживать."),
        ]
    if lead_quality == "weak":
        return tr("Improve lead quality", "Улучшите качество обращений"), [
            tr("The platform may be finding cheap but low-value conversations.", "Реклама может приводить дешёвые, но слабые по качеству обращения."),
        ]
    if break_even_cac <= 0:
        return tr("Improve margin first", "Сначала увеличьте прибыль с заказа"), [
            tr("The first-order economics do not currently support paid acquisition.", "Экономика первого заказа сейчас не поддерживает платное привлечение."),
        ]
    if real_cac and target_cac > 0 and real_cac <= target_cac * 0.85:
        return tr("Scale gradually", "Увеличивайте бюджет постепенно"), [
            tr("Real CAC is below target CAC with enough evidence to expand carefully.", "Реальная стоимость привлечения клиента ниже целевого уровня, и данных уже достаточно для аккуратного роста."),
        ]
    if real_cac and break_even_cac > 0 and real_cac > break_even_cac:
        return tr("Reduce spend", "Снизьте бюджет"), [
            tr("Real CAC is above break-even CAC, so current growth is destroying profit.", "Реальная стоимость привлечения клиента выше уровня безубыточности, поэтому текущий рост уничтожает прибыль."),
        ]
    return tr("Hold current spend", "Оставьте текущий бюджет"), [
        tr("Keep collecting data or improve conversion before scaling harder.", "Продолжайте собирать данные или сначала улучшите продажи."),
    ]


# =========================
# V2 App Flow
# =========================
analysis_goal_options = [
    ("validate_product", tr("Validate a new product", "Проверить новый товар или услугу")),
    ("test_campaign", tr("Test a campaign", "Проверить рекламу")),
    ("ads_profitability", tr("Understand if current ads are profitable", "Понять, приносит ли реклама прибыль")),
    ("decide_scale", tr("Decide whether to scale", "Решить, стоит ли увеличивать бюджет")),
    ("audit_expensive", tr("Audit why ads feel expensive", "Понять, почему реклама выходит дорогой")),
]
analysis_goal_map = dict(analysis_goal_options)

st.subheader(tr("What are you trying to do?", "Что вы хотите сделать?"))
analysis_goal = st.radio(
    "",
    options=[key for key, _ in analysis_goal_options],
    format_func=analysis_goal_map.get,
    horizontal=False,
    label_visibility="collapsed",
)

st.divider()
st.subheader(tr("Business context", "Информация о бизнесе"))

business_name = st.text_input(tr("Business name", "Название бизнеса"))

industry_options = [
    ("ecommerce", tr("E-commerce", "E-commerce")),
    ("services", tr("Services", "Услуги")),
    ("education", tr("Education", "Образование")),
    ("health_beauty", tr("Здоровье / красота", "Здоровье / красота")),
    ("b2b", tr("B2B", "B2B")),
    ("other", tr("Other", "Другое")),
]
sales_channel_options = [
    ("website", tr("Оплата на сайте", "Покупка на сайте")),
    ("messaging", tr("WhatsApp / Telegram / личные сообщения", "WhatsApp / Telegram / личные сообщения")),
    ("consultation", tr("Звонок / консультация", "Звонок / консультация")),
    ("mixed", tr("Mixed", "Несколько способов")),
]
sales_cycle_options = [
    ("same_day", tr("Same day", "В тот же день")),
    ("days_2_7", tr("2-7 days", "2–7 дней")),
    ("weeks_1_2", tr("1-2 weeks", "1–2 недели")),
    ("longer", tr("Longer", "Дольше")),
]

ctx1, ctx2, ctx3 = st.columns(3)
with ctx1:
    industry = st.selectbox(
        tr("Сфера бизнеса", "Сфера бизнеса"),
        options=[key for key, _ in industry_options],
        format_func=dict(industry_options).get,
    )
with ctx2:
    sales_channel = st.selectbox(
        tr("Sales channel", "Как вы продаёте"),
        options=[key for key, _ in sales_channel_options],
        format_func=dict(sales_channel_options).get,
    )
with ctx3:
    sales_cycle = st.selectbox(
        tr("Sales cycle", "Сколько обычно длится продажа"),
        options=[key for key, _ in sales_cycle_options],
        format_func=dict(sales_cycle_options).get,
    )

repeat_purchase_default = st.radio(
    tr("Repeat purchase?", "Клиенты покупают повторно?"),
    options=["no", "yes"],
    format_func=lambda x: tr("No", "Нет") if x == "no" else tr("Yes", "Да"),
    horizontal=True,
)

st.divider()
st.subheader(tr("How do you want to analyze?", "Как хотите посчитать?"))

source_options = [
    ("upload_meta_report", tr("Upload Meta CSV/XLSX", "Загрузить рекламный отчёт")),
    ("manual_inputs_only", tr("Enter manually", "Ввести вручную")),
    ("новый_бизнес_assumptions_only", tr("New business / no campaign data yet", "Новый бизнес / пока нет данных по рекламе")),
]
source_key = st.radio(
    "",
    options=[key for key, _ in source_options],
    format_func=dict(source_options).get,
    horizontal=True,
    label_visibility="collapsed",
)

reported_spend = 0.0
reported_results = 0.0
reported_result_type = tr("Not detected", "Не определён")
detected_campaigns = 0
selected_campaigns = []
actual_paid_spend = 0.0
true_spend = 0.0
spend_reason = "none"
real_conversations = 0.0
qualified_leads = 0.0
real_orders = 0.0
refund_count = 0.0
lead_quality = "mixed"
aov = 0.0
cogs_per_order = 0.0
refund_rate_pct = 0.0
desired_profit_per_order = 0.0
max_acceptable_cac_pct_of_price = 0.0
repeat_purchase_value = 0.0
close_rate = 0.0
close_rate_confidence = "medium"
close_rate_source = "guess"
real_lead_definition = "осмысленное_обращение"
target_conversations = 20.0
goal_type = analysis_goal
budget_tolerance = "moderate"
cost_per_reported_result = 0.0
cost_per_conversation = 0.0
estimated_cac = 0.0
real_cac = None
break_even_cac = 0.0
target_cac = 0.0
gross_margin_pct = 0.0
refund_adjusted_margin = 0.0
target_cac_pct_of_price = 0.0
max_cost_per_conversation = 0.0
recommended_test_budget = 0.0
meta_counts_reflect_real = True
spend_overhead_pct = 0.0
used_conversations = 0.0
mode_key = "новый_бизнес" if source_key == "новый_бизнес_assumptions_only" else "ранний_тест"
confidence_label = tr("Low", "Низкая")
confidence_reasons = []
has_economics = False
spend_is_adjusted = False
recommendation_headline = ""
recommendation_points = []
low_confidence = True

if source_key == "новый_бизнес_assumptions_only":
    st.divider()
    st.subheader(tr("Plan a first test", "План первого теста"))

    nb1, nb2, nb3 = st.columns(3)
    with nb1:
        aov = st.number_input(money_label(tr("Средний чек", "Средний чек")), min_value=0.0, value=120.0)
        cogs_per_order = st.number_input(money_label(tr("Себестоимость одного заказа", "Себестоимость одного заказа")), min_value=0.0, value=45.0)
        refund_rate_pct = st.number_input(tr("Refund rate (%)", "Процент возвратов (%)"), min_value=0.0, max_value=100.0, value=5.0)
    with nb2:
        close_rate = st.number_input(tr("Expected close rate from conversation to order", "Ожидаемая конверсия в покупку"), min_value=0.0, max_value=1.0, value=0.2)
        expected_cost_per_conversation = st.number_input(money_label(tr("Ожидаемая стоимость обращения", "Ожидаемая стоимость обращения")), min_value=0.0, value=3.5)
        expected_cac_input = st.number_input(money_label(tr("Ожидаемая стоимость привлечения клиента (необязательно)", "Ожидаемая стоимость привлечения клиента (необязательно)")), min_value=0.0, value=0.0)
    with nb3:
        desired_profit_per_order = st.number_input(money_label(tr("Желаемая прибыль с заказа", "Желаемая прибыль с заказа")), min_value=0.0, value=10.0)
        assumption_source = st.selectbox(
            tr("Assumption source", "Откуда взяты предположения"),
            options=["guess", "benchmark", "experience"],
            format_func=lambda x: {
                "guess": tr("Guess", "Предположение"),
                "benchmark": tr("Competitor benchmark", "Ориентир по конкурентам"),
                "experience": tr("Previous experience", "Ваш прошлый опыт"),
            }[x],
        )
        close_rate_source = "guess" if assumption_source == "guess" else "past_campaigns"

    threshold_option = st.selectbox(
        tr("How many conversations before judging?", "Сколько обращений собрать до оценки?"),
        options=[10, 20, 30, "custom"],
        format_func=lambda x: tr("Custom", "Свой") if x == "custom" else str(x),
    )
    if threshold_option == "custom":
        target_conversations = float(
            st.number_input(tr("Custom target conversations", "Свой порог обращений"), min_value=1, value=20)
        )
    else:
        target_conversations = float(threshold_option)

    repeat_purchase_value = 0.0
    if repeat_purchase_default == "yes":
        repeat_purchase_value = st.number_input(
            tr("Expected repeat value / LTV uplift ($)", "Ожидаемая повторная выручка"),
            min_value=0.0,
            value=0.0,
        )

    break_even_cac = aov - cogs_per_order - (aov * refund_rate_pct / 100.0)
    target_cac = break_even_cac - desired_profit_per_order
    gross_margin_pct = safe_div(aov - cogs_per_order, aov) * 100 if aov > 0 else 0.0
    refund_adjusted_margin = break_even_cac
    target_cac_pct_of_price = safe_div(target_cac, aov) * 100 if aov > 0 else 0.0
    estimated_cac = expected_cac_input if expected_cac_input > 0 else safe_div(expected_cost_per_conversation, close_rate)
    max_cost_per_conversation = max(target_cac, 0.0) * close_rate
    recommended_test_budget = expected_cost_per_conversation * target_conversations
    scenario_orders = safe_div(recommended_test_budget, estimated_cac) if estimated_cac > 0 else 0.0
    scenario_revenue = scenario_orders * aov
    scenario_profit = scenario_orders * (aov - cogs_per_order - (aov * refund_rate_pct / 100.0) - estimated_cac)
    used_conversations = 0.0
    has_economics = aov > 0 and cogs_per_order >= 0
    mode_key = "новый_бизнес"
    confidence_label, confidence_reasons = get_confidence_v2(
        source_key=source_key,
        used_conversations=used_conversations,
        real_orders=0.0,
        threshold=max(target_conversations, 10.0),
        close_rate_source=close_rate_source,
        spend_is_adjusted=False,
        has_economics=has_economics,
        lead_quality="mixed",
    )
    recommendation_headline, recommendation_points = get_recommendation_v2(
        mode_key=mode_key,
        true_spend=0.0,
        reported_spend=0.0,
        used_conversations=used_conversations,
        qualified_leads=0.0,
        real_orders=0.0,
        refund_count=0.0,
        lead_quality="mixed",
        break_even_cac=break_even_cac,
        target_cac=target_cac,
        cost_per_conversation=expected_cost_per_conversation,
        estimated_cac=estimated_cac,
        real_cac=None,
        max_cost_per_conversation=max_cost_per_conversation,
        recommended_test_budget=recommended_test_budget,
        target_conversations=target_conversations,
        close_rate_source=close_rate_source,
    )
    low_confidence = True

    st.divider()
    st.subheader(tr("Decision", "Решение"))
    st.markdown(f'<div class="big-status fragile">{tr("Предварительный расчёт на основе предположений", "Сценарий на основе предположений")}</div>', unsafe_allow_html=True)

    st.warning(
        tr(
            "Анализ с низкой надёжностью\n\nThis result is based on assumptions and/or incomplete downstream data. Use it for planning and validation, not as proof of profitability.",
            "Низкая надёжность анализа\n\nЭтот результат основан на предположениях и/или неполных данных ниже по воронке. Используйте его для планирования и валидации, а не как доказательство прибыльности.",
        )
    )

    b1, b2, b3 = st.columns(3)
    b1.metric(tr("Break-even CAC", "Стоимость клиента без убытка"), format_money(break_even_cac))
    b2.metric(tr("Target CAC", "Желаемая стоимость клиента"), format_money(target_cac))
    b3.metric(tr("Max cost per conversation", "Максимальная стоимость обращения"), format_money(max_cost_per_conversation))

    b4 = st.columns(1)[0]
    b4.metric(tr("Бюджет на тест", "Бюджет на валидацию"), format_money(recommended_test_budget))

    with st.expander(tr("Illustrative scenario only", "Примерный расчёт"), expanded=False):
        st.write(f"**{tr('If assumptions hold', 'Если предположения верны')}:**")
        st.write(f"- {tr('Illustrative orders', 'Примерное число заказов')}: **{scenario_orders:.1f}**")
        st.write(f"- {tr('Illustrative revenue', 'Примерная выручка')}: **{format_money(scenario_revenue)}**")
        st.write(f"- {tr('Illustrative profit', 'Примерная прибыль')}: **{format_money(scenario_profit)}**")

    st.subheader(tr("How reliable this analysis is", "Насколько надёжен этот анализ"))
    st.write(f"**{confidence_label}**")
    for reason in confidence_reasons:
        st.write(f"- {reason}")

    st.subheader(tr("What to do next", "Что делать дальше"))
    st.info(recommendation_headline)
    for point in recommendation_points:
        st.write(f"- {point}")

    st.subheader(tr("Key answers", "Ключевые ответы"))
    st.write(f"1. {tr('Can this business support ads in theory?', 'Может ли бизнес в теории выдержать рекламу?')} {tr('Yes, if CAC stays at or below', 'Да, если стоимость клиента держится на уровне или ниже')} **{format_money(max(target_cac, 0.0))}**.")
    st.write(f"2. {tr('Is the current data enough to judge?', 'Достаточно ли данных для вывода?')} {tr('No, this is still an assumption-based plan.', 'Нет, это пока сценарий на предположениях.')}")
    st.write(f"3. {tr('How much should be spent next to get evidence?', 'Сколько потратить дальше, чтобы получить доказательства?')} **{format_money(recommended_test_budget)}**.")
    st.write(f"4. {tr('Should we scale?', 'Стоит ли увеличивать бюджет?')} {tr('Not yet. Validate the assumptions first.', 'Пока нет. Сначала проверьте предположения на практике.')}")

else:
    tab_upload, tab_reality, tab_economics, tab_decision = st.tabs(
        [
            tr("① Upload & detect", "① Загрузка и данные"),
            tr("② Reality check", "② Проверка реальности"),
            tr("③ Economics", "③ Экономика"),
            tr("④ Decision", "④ Решение"),
        ]
    )

    with tab_upload:
        st.caption(tr("Step 1 of 4 — Enter your campaign source data. Then move to ② Reality check.", "Шаг 1 из 4 — Введите данные по рекламе. Затем перейдите в ② Проверка реальности."))
        st.subheader(tr("Campaign source", "Откуда взять данные по рекламе"))

        if source_key == "upload_meta_report":
            uploaded = st.file_uploader(tr("Upload file", "Загрузить файл отчёта"), type=["csv", "xlsx", "xls"])
            if not uploaded:
                st.info(tr("Upload a Meta report to detect spend and results.", "Загрузите рекламный отчёт, чтобы определить расходы и результаты."))
            else:
                try:
                    df = read_uploaded_report(uploaded)
                    st.write(tr("Preview first rows", "Первые строки"))
                    st.dataframe(df.head(10), use_container_width=True)

                    cols = list(df.columns)
                    col_campaign = st.selectbox(
                        tr("Campaign name", "Название рекламной кампании"),
                        cols,
                        index=guess_index_from_patterns(cols, ["Campaign name", "Campaign", "campaign_name"]),
                    )
                    col_spend = st.selectbox(
                        tr("Spend", "Расход"),
                        cols,
                        index=guess_index_from_patterns(cols, ["Amount spent (MYR)", "Amount spent", "Spend", "Amount spent (USD)"]),
                    )
                    col_results = st.selectbox(
                        tr("Results", "Результаты"),
                        cols,
                        index=guess_index_from_patterns(cols, ["Results", "Result", "results"]),
                    )
                    col_indicator = st.selectbox(
                        tr("Result indicator", "Тип результата"),
                        cols,
                        index=guess_index_from_patterns(cols, ["Result indicator", "Action type", "Result type", "result_indicator"]),
                    )

                    indicator_series = df[col_indicator].astype(str).str.lower()
                    msg_mask = (
                        indicator_series.str.contains("messaging", na=False)
                        | indicator_series.str.contains("conversation", na=False)
                        | indicator_series.str.contains("message", na=False)
                    )
                    df_msg = df[msg_mask].copy()
                    if df_msg.empty:
                        st.warning(t["msg_fallback_all"])
                        df_msg = df.copy()

                    campaigns = sorted(df_msg[col_campaign].dropna().astype(str).unique().tolist())
                    selected_campaigns = st.multiselect(
                        tr("Select campaigns to include", "Выберите рекламные кампании"),
                        campaigns,
                        default=campaigns,
                    )
                    if selected_campaigns:
                        df_msg = df_msg[df_msg[col_campaign].astype(str).isin(selected_campaigns)].copy()

                    df_msg[col_spend] = parse_number_series(df_msg[col_spend])
                    df_msg[col_results] = parse_number_series(df_msg[col_results])

                    reported_spend = float(df_msg[col_spend].sum())
                    reported_results = float(df_msg[col_results].sum())
                    detected_campaigns = len(selected_campaigns) if selected_campaigns else len(campaigns)

                    unique_indicator_values = sorted(df[col_indicator].dropna().astype(str).unique().tolist())
                    # Build result type sample from the filtered (messaging + selected campaigns) data,
                    # not from the full original df — otherwise it shows unrelated result types.
                    filtered_indicator_values = sorted(df_msg[col_indicator].dropna().astype(str).unique().tolist())
                    sample_values = filtered_indicator_values[:5]
                    reported_result_type = ", ".join(sample_values) if sample_values else tr("Not detected", "Не определён")
                    cost_per_reported_result = safe_div(reported_spend, reported_results)

                    s1, s2, s3, s4 = st.columns(4)
                    s1.metric(tr("Reported spend", "Расход по отчёту"), format_money(reported_spend))
                    s2.metric(tr("Reported results", "Результаты по отчёту"), f"{reported_results:.1f}")
                    s3.metric(tr("Campaigns found", "Найдено кампаний"), detected_campaigns)
                    s4.metric(tr("Cost per reported result", "Стоимость reported result"), format_money(cost_per_reported_result))

                    st.write(f"**{tr('Detected result type sample', 'Пример найденных типов результата')}:** {reported_result_type}")
                    st.write(tr("Unique indicator values", "Уникальные значения индикатора"))
                    st.dataframe(pd.DataFrame({col_indicator: unique_indicator_values}), use_container_width=True)
                except Exception as e:
                    st.error(f"{tr('Could not read the uploaded file.', 'Не удалось прочитать файл.')} {e}")

        else:
            st.caption(tr("Manual path for current campaign data.", "Ручной путь для данных текущей кампании."))
            m1, m2, m3 = st.columns(3)
            with m1:
                reported_spend = st.number_input(tr("Reported ad spend ($)", "Расход по отчёту ($)"), min_value=0.0, value=0.0)
            with m2:
                reported_results = st.number_input(tr("Meta-reported conversations", "Диалоги по данным Meta"), min_value=0.0, value=0.0)
            with m3:
                reported_result_type = st.text_input(tr("Reported result type", "Тип результата в отчёте"), value=tr("Conversation", "Диалог"))
            cost_per_reported_result = safe_div(reported_spend, reported_results)
            detected_campaigns = 1 if reported_spend > 0 or reported_results > 0 else 0

        meta_counts_reflect_real = st.radio(
            tr("Does Meta's result count reflect real business conversations?", "Отражает ли результат Meta реальные бизнес-диалоги?"),
            options=["yes", "no"],
            format_func=lambda x: tr("Yes", "Да") if x == "yes" else tr("No, I want to adjust it manually", "Нет, я хочу скорректировать это вручную"),
            horizontal=False,
        ) == "yes"

    with tab_reality:
        st.caption(tr("Step 2 of 4 — Correct Meta data with real numbers from your CRM/inbox. Then move to ③ Economics.", "Шаг 2 из 4 — Скорректируйте данные Meta реальными цифрами из CRM/инбокса. Затем перейдите на ③ Экономика."))
        st.subheader(tr("Correct Meta data with real business numbers", "Скорректируйте данные Meta реальными бизнес-данными"))

        default_paid_spend = reported_spend
        actual_paid_spend = st.number_input(
            tr("Actual amount paid ($)", "Фактически оплаченная сумма ($)"),
            min_value=0.0,
            value=float(default_paid_spend),
        )
        # Explicit override flag: lets user set spend to $0 intentionally.
        # Without this, entering 0 was silently ignored and reported_spend was reused.
        spend_override_active = st.checkbox(
            tr(
                "Override detected spend with the value above (including if it's $0)",
                "Использовать введённое значение вместо автоопределённого (включая $0)",
            ),
            value=False,
        )
        spend_reason = st.selectbox(
            tr("Difference reason", "Причина расхождения"),
            options=["none", "vat", "currency", "topup", "agency", "other"],
            format_func=lambda x: {
                "none": tr("No adjustment", "Без корректировки"),
                "vat": tr("VAT / tax", "НДС / налог"),
                "currency": tr("Currency conversion", "Конвертация валюты"),
                "topup": tr("Top-up fee", "Комиссия пополнения"),
                "agency": tr("Agency fee", "Комиссия агентства"),
                "other": tr("Other", "Другое"),
            }[x],
        )

        default_real_conversations = reported_results if meta_counts_reflect_real else 0.0
        real_conversations = st.number_input(
            tr("Actual meaningful conversations", "Реальные meaningful conversations"),
            min_value=0.0,
            value=float(default_real_conversations),
        )
        # Explicit override flag: lets user intentionally set conversations to 0.
        # Without this, entering 0 was silently ignored and reported_results was reused.
        convo_override_active = st.checkbox(
            tr(
                "Override Meta's conversation count with the value above (including if it's 0)",
                "Использовать введённое количество диалогов вместо данных Meta (включая 0)",
            ),
            value=meta_counts_reflect_real,
        )
        qualified_leads = st.number_input(tr("Qualified leads", "Квалифицированные обращения"), min_value=0.0, value=0.0)
        real_orders = st.number_input(tr("Orders", "Заказы"), min_value=0.0, value=0.0)
        refund_count = st.number_input(tr("Refunds / cancellations", "Возвраты / отмены"), min_value=0.0, value=0.0)
        lead_quality = st.selectbox(
            tr("Lead quality", "Качество лидов"),
            options=["weak", "mixed", "strong"],
            format_func=lambda x: {
                "weak": tr("Weak", "Слабое"),
                "mixed": tr("Mixed", "Смешанное"),
                "strong": tr("Strong", "Сильное"),
            }[x],
        )

        # Use override values when the user explicitly opted in; otherwise fall back to reported values.
        true_spend = actual_paid_spend if spend_override_active else (actual_paid_spend if actual_paid_spend > 0 else reported_spend)
        used_conversations = real_conversations if convo_override_active else (real_conversations if real_conversations > 0 else reported_results)
        spend_is_adjusted = abs(actual_paid_spend - reported_spend) > 0.009
        spend_overhead_pct = safe_div(true_spend - reported_spend, reported_spend) * 100 if reported_spend > 0 else 0.0

        r1, r2, r3, r4 = st.columns(4)
        r1.metric(tr("Reported spend", "Расход по отчёту"), format_money(reported_spend))
        r2.metric(tr("Actual paid spend", "Фактически оплачено"), format_money(true_spend))
        r3.metric(tr("Used conversations", "Используемые диалоги"), f"{used_conversations:.1f}")
        r4.metric(tr("Spend overhead %", "Оверхед по расходу %"), f"{spend_overhead_pct:.1f}%")

    with tab_economics:
        st.caption(tr("Step 3 of 4 — Fill in your unit economics. Then move to ④ Decision.", "Шаг 3 из 4 — Заполните юнит-экономику. Затем перейдите на ④ Решение."))
        st.subheader(tr("Business economics", "Экономика бизнеса"))

        e1, e2, e3 = st.columns(3)
        with e1:
            aov = st.number_input(money_label(tr("Средний чек", "Средний чек")), min_value=0.0, value=0.0)
            cogs_per_order = st.number_input(money_label(tr("Себестоимость одного заказа", "Себестоимость одного заказа")), min_value=0.0, value=0.0)
        with e2:
            refund_rate_pct = st.number_input(tr("Refund rate (%)", "Процент возвратов (%)"), min_value=0.0, max_value=100.0, value=0.0)
            desired_profit_per_order = st.number_input(money_label(tr("Желаемая прибыль с заказа", "Желаемая прибыль с заказа")), min_value=0.0, value=0.0)
        with e3:
            max_acceptable_cac_pct_of_price = st.number_input(
                tr("Max acceptable CAC as % of price", "Максимально допустимый CAC как % от цены"),
                min_value=0.0,
                max_value=500.0,
                value=0.0,
            )

        repeat_purchase_value = 0.0
        if repeat_purchase_default == "yes":
            repeat_purchase_value = st.number_input(
                tr("Expected repeat value / LTV uplift ($)", "Ожидаемая повторная выручка"),
                min_value=0.0,
                value=0.0,
            )

        close_rate = st.number_input(
            tr("Close rate from conversation to order", "Конверсия в покупку"),
            min_value=0.0,
            max_value=1.0,
            value=0.20,
        )
        close_rate_confidence = st.selectbox(
            tr("Confidence in close rate", "Уверенность в close rate"),
            options=["low", "medium", "high"],
            format_func=lambda x: {
                "low": tr("Low", "Низкая"),
                "medium": tr("Medium", "Средняя"),
                "high": tr("High", "Высокая"),
            }[x],
        )
        close_rate_source = st.selectbox(
            tr("Close rate is based on", "Close rate основан на"),
            options=["real_data", "past_campaigns", "guess"],
            format_func=lambda x: {
                "real_data": tr("Real history", "Реальные данные"),
                "past_campaigns": tr("Previous campaigns", "Предыдущие кампании"),
                "guess": tr("Guess", "Предположение"),
            }[x],
        )
        real_lead_definition = st.selectbox(
            tr("What counts as a real lead?", "Что считать реальным лидом?"),
            options=["any_conversation", "осмысленное_обращение", "qualified_lead", "consultation_booked"],
            format_func=lambda x: {
                "any_conversation": tr("Any conversation", "Любой диалог"),
                "осмысленное_обращение": tr("Meaningful conversation", "Осмысленный диалог"),
                "qualified_lead": tr("Qualified lead", "Квалифицированный лид"),
                "consultation_booked": tr("Booked consultation", "Назначенная консультация"),
            }[x],
        )
        threshold_option = st.selectbox(
            tr("How many conversations do you want before judging the campaign?", "Сколько диалогов нужно до оценки кампании?"),
            options=[10, 20, 30, "custom"],
            format_func=lambda x: tr("Custom", "Свой") if x == "custom" else str(x),
        )
        if threshold_option == "custom":
            target_conversations = float(
                st.number_input(tr("Custom target conversations", "Свой порог обращений"), min_value=1, value=20)
            )
        else:
            target_conversations = float(threshold_option)

        goal_type = st.selectbox(
            tr("What is your goal?", "Какова ваша цель?"),
            options=["validate_product", "break_even", "small_profit", "aggressive_growth"],
            format_func=lambda x: {
                "validate_product": tr("Validate demand", "Проверить спрос"),
                "break_even": tr("Break even", "Выйти в ноль"),
                "small_profit": tr("Small first-order profit", "Небольшая прибыль с первого заказа"),
                "aggressive_growth": tr("Aggressive growth", "Агрессивный рост"),
            }[x],
        )
        budget_tolerance = st.selectbox(
            tr("Budget tolerance", "Допуск по бюджету"),
            options=["conservative", "moderate", "aggressive"],
            format_func=lambda x: {
                "conservative": tr("Conservative", "Консервативный"),
                "moderate": tr("Moderate", "Умеренный"),
                "aggressive": tr("Aggressive", "Агрессивный"),
            }[x],
        )

        refund_cost = aov * refund_rate_pct / 100.0
        break_even_cac = aov - cogs_per_order - refund_cost
        target_cac = break_even_cac - desired_profit_per_order
        gross_margin_pct = safe_div(aov - cogs_per_order, aov) * 100 if aov > 0 else 0.0
        refund_adjusted_margin = break_even_cac
        target_cac_pct_of_price = safe_div(target_cac, aov) * 100 if aov > 0 else 0.0
        cost_per_conversation = safe_div(true_spend, used_conversations)
        estimated_cac = safe_div(cost_per_conversation, close_rate)
        real_cac = safe_div(true_spend, real_orders) if real_orders > 0 else None
        max_cost_per_conversation = max(target_cac, 0.0) * close_rate
        recommended_test_budget = target_conversations * cost_per_conversation
        has_economics = aov > 0 and cogs_per_order >= 0

        e4, e5, e6 = st.columns(3)
        e4.metric(tr("Gross margin %", "Валовая маржа %"), f"{gross_margin_pct:.1f}%")
        e5.metric(tr("Break-even CAC", "Стоимость клиента без убытка"), format_money(break_even_cac))
        e6.metric(tr("Target CAC", "Желаемая стоимость клиента"), format_money(target_cac))

        e7, e8, e9 = st.columns(3)
        e7.metric(tr("Cost per conversation", "Стоимость диалога"), format_money(cost_per_conversation))
        e8.metric(tr("Estimated CAC", "Расчётная стоимость клиента"), format_money(estimated_cac))
        e9.metric(tr("Max cost per conversation", "Максимальная стоимость обращения"), format_money(max_cost_per_conversation))

    mode_key = classify_mode_v2(
        source_key=source_key,
        used_conversations=used_conversations,
        real_orders=real_orders,
        threshold=target_conversations,
        close_rate_confidence=close_rate_confidence,
        close_rate_source=close_rate_source,
        has_economics=has_economics,
        true_spend=true_spend,
    )
    confidence_label, confidence_reasons = get_confidence_v2(
        source_key=source_key,
        used_conversations=used_conversations,
        real_orders=real_orders,
        threshold=target_conversations,
        close_rate_source=close_rate_source,
        spend_is_adjusted=spend_is_adjusted,
        has_economics=has_economics,
        lead_quality=lead_quality,
    )
    low_confidence = is_low_confidence_v2(
        source_key=source_key,
        mode_key=mode_key,
        real_orders=real_orders,
        close_rate_source=close_rate_source,
        used_conversations=used_conversations,
        threshold=target_conversations,
    )
    recommendation_headline, recommendation_points = get_recommendation_v2(
        mode_key=mode_key,
        true_spend=true_spend,
        reported_spend=reported_spend,
        used_conversations=used_conversations,
        qualified_leads=qualified_leads,
        real_orders=real_orders,
        refund_count=refund_count,
        lead_quality=lead_quality,
        break_even_cac=break_even_cac,
        target_cac=target_cac,
        cost_per_conversation=cost_per_conversation,
        estimated_cac=estimated_cac,
        real_cac=real_cac,
        max_cost_per_conversation=max_cost_per_conversation,
        recommended_test_budget=recommended_test_budget,
        target_conversations=target_conversations,
        close_rate_source=close_rate_source,
    )

    with tab_decision:
        # Guard: show a prompt if no meaningful data has been entered yet.
        # Allow zero spend (audit / planning use case) as long as economics are filled.
        _data_ready = aov > 0
        if not _data_ready:
            st.info(
                tr(
                    "⬅️ Fill in tabs ①, ②, and ③ first — at minimum enter AOV in ③ Economics — then come back here for your decision.",
                    "⬅️ Сначала заполните вкладки ①, ② и ③ — как минимум укажите средний чек в ③ Экономика — затем вернитесь сюда за выводом.",
                )
            )
            st.stop()
        st.subheader(tr("Decision", "Решение"))
        mode_label = {
            "новый_бизнес": tr("New Business", "Новый бизнес"),
            "ранний_тест": tr("Early test", "Ранний тест"),
            "данных_достаточно": tr("Validated", "Подтверждённый режим"),
        }.get(mode_key, tr("Early test", "Ранний тест"))
        mode_badge_class = "fragile" if mode_key == "ранний_тест" else "safe"
        st.markdown(f'<div class="big-status {mode_badge_class}">{mode_label}</div>', unsafe_allow_html=True)

        meta_col, biz_col = st.columns(2)
        with meta_col:
            st.subheader(tr("What Meta reports", "Что сообщает Meta"))
            st.metric(tr("Reported spend", "Расход по отчёту"), format_money(reported_spend))
            st.metric(tr("Reported results", "Результаты по отчёту"), f"{reported_results:.1f}")
            st.metric(tr("Result type", "Тип результата"), reported_result_type[:32] if reported_result_type else tr("n/a", "н/д"))
            st.metric(tr("Cost per reported result", "Стоимость reported result"), format_money(cost_per_reported_result))
        with biz_col:
            st.subheader(tr("What the business actually saw", "Что бизнес увидел на самом деле"))
            st.metric(tr("Actual paid spend", "Фактически оплачено"), format_money(true_spend))
            st.metric(tr("Real conversations", "Реальные диалоги"), f"{used_conversations:.1f}")
            st.metric(tr("Qualified leads", "Квалифицированные обращения"), f"{qualified_leads:.1f}")
            st.metric(tr("Orders", "Заказы"), f"{real_orders:.1f}")
            st.metric(
                tr("Lead quality", "Качество лидов"),
                tr("Weak", "Слабое") if lead_quality == "weak" else tr("Mixed", "Смешанное") if lead_quality == "mixed" else tr("Strong", "Сильное"),
            )
            st.write(f"**{tr('Spend overhead %', 'Оверхед по расходу %')}:** {spend_overhead_pct:.1f}%")
            st.write(
                f"**{tr('Reason for difference', 'Причина расхождения')}:** "
                f"{ {'none': tr('No adjustment', 'Без корректировки'), 'vat': tr('VAT / tax', 'НДС / налог'), 'currency': tr('Currency conversion', 'Конвертация валюты'), 'topup': tr('Top-up fee', 'Комиссия пополнения'), 'agency': tr('Agency fee', 'Комиссия агентства'), 'other': tr('Other', 'Другое')}[spend_reason] }"
            )

        if low_confidence:
            st.warning(
                tr(
                    "Анализ с низкой надёжностью\n\nThis result is based on assumptions and/or incomplete downstream data. Use it for planning and validation, not as proof of profitability.",
                    "Низкая надёжность анализа\n\nЭтот результат основан на предположениях и/или неполных данных ниже по воронке. Используйте его для планирования и валидации, а не как доказательство прибыльности.",
                )
            )

        st.subheader(tr("Funnel comparison", "Сравнение воронки"))
        f1, f2, f3, f4 = st.columns(4)
        f1.metric(tr("Meta reported conversations", "Диалоги по данным Meta"), f"{reported_results:.1f}")
        f2.metric(tr("Real conversations", "Реальные диалоги"), f"{used_conversations:.1f}")
        f3.metric(tr("Qualified leads", "Квалифицированные обращения"), f"{qualified_leads:.1f}")
        f4.metric(tr("Orders", "Заказы"), f"{real_orders:.1f}")

        fp1, fp2, fp3 = st.columns(3)
        fp1.metric(
            tr("Real conversations / Meta reported", "Реальные диалоги / Meta reported"),
            f"{safe_div(used_conversations, reported_results) * 100:.1f}%" if reported_results > 0 else tr("n/a", "н/д"),
        )
        fp2.metric(
            tr("Qualified leads / Real conversations", "Квал. обращения / Реальные диалоги"),
            f"{safe_div(qualified_leads, used_conversations) * 100:.1f}%" if used_conversations > 0 else tr("n/a", "н/д"),
        )
        base_for_orders = qualified_leads if qualified_leads > 0 else used_conversations
        fp3.metric(
            tr("Orders / Qualified", "Заказы / Квал."),
            f"{safe_div(real_orders, base_for_orders) * 100:.1f}%" if base_for_orders > 0 else tr("n/a", "н/д"),
        )

        st.subheader(tr("Business economics", "Экономика бизнеса"))
        x1, x2, x3 = st.columns(3)
        x1.metric("AOV", format_money(aov))
        x2.metric(tr("COGS", "COGS"), format_money(cogs_per_order))
        x3.metric(tr("Gross margin %", "Валовая маржа %"), f"{gross_margin_pct:.1f}%")
        x4, x5 = st.columns(2)
        x4.metric(tr("Break-even CAC", "Стоимость клиента без убытка"), format_money(break_even_cac))
        x5.metric(tr("Target CAC", "Желаемая стоимость клиента"), format_money(target_cac))
        st.write(f"**{tr('CAC as % of price', 'CAC как % от цены')}:** {target_cac_pct_of_price:.1f}%")
        st.write(f"**{tr('Max cost per conversation', 'Максимальная стоимость обращения')}:** {format_money(max_cost_per_conversation)}")

        budget_header = tr("Recommended test budget", "Рекомендуемый бюджет на тест")
        st.subheader(budget_header)
        tb1, tb2, tb3, tb4 = st.columns(4)
        tb1.metric(tr("Budget for 10 conversations", "Бюджет на 10 диалогов"), format_money(cost_per_conversation * 10))
        tb2.metric(tr("Budget for 20 conversations", "Бюджет на 20 диалогов"), format_money(cost_per_conversation * 20))
        tb3.metric(tr("Budget for 30 conversations", "Бюджет на 30 диалогов"), format_money(cost_per_conversation * 30))
        tb4.metric(tr("Budget for selected threshold", "Бюджет под выбранный порог"), format_money(recommended_test_budget))

        st.subheader(tr("How reliable this analysis is", "Насколько надёжен этот анализ"))
        st.write(f"**{tr('Confidence level', 'Уровень уверенности')}: {confidence_label}**")
        for reason in confidence_reasons:
            st.write(f"- {reason}")

        st.subheader(tr("What to do next", "Что делать дальше"))
        st.info(recommendation_headline)
        for point in recommendation_points:
            st.write(f"- {point}")

        if mode_key == "ранний_тест":
            st.subheader(tr("Track next", "Отслеживать дальше"))
            st.info(
                tr(
                    "Operational checklist for the next review cycle.",
                    "Операционный чек-лист к следующему циклу проверки.",
                )
            )
            for item in [
                tr("Actual paid spend", "Фактически оплаченный расход"),
                tr("Real conversations", "Реальные диалоги"),
                tr("Qualified leads", "Квалифицированные обращения"),
                tr("First orders", "Первые заказы"),
                tr("Refunds / cancellations", "Возвраты / отмены"),
            ]:
                st.write(f"- {item}")

        st.subheader(tr("Key answers", "Ключевые ответы"))
        theory_answer = (
            tr("Yes, if CAC stays below target CAC.", "Да, если CAC держится ниже целевого CAC.")
            if target_cac > 0
            else tr("Not yet. The first-order economics do not currently support ads.", "Пока нет. Экономика первого заказа пока не поддерживает рекламу.")
        )
        data_answer = (
            tr("Yes, there is enough downstream evidence to judge.", "Да, данных ниже по воронке уже достаточно для оценки.")
            if mode_key == "данных_достаточно"
            else tr("Not yet. Gather more real conversations and orders first.", "Пока нет. Сначала соберите больше реальных диалогов и заказов.")
        )
        next_budget_answer = (
            format_money(recommended_test_budget)
            if recommended_test_budget > 0
            else tr("Need conversation cost first.", "Сначала нужна стоимость диалога.")
        )
        scale_answer = {
            "данных_достаточно": recommendation_headline,
            "ранний_тест": tr("Too early to judge profitability.", "Слишком рано судить о прибыльности."),
            "новый_бизнес": tr("Not yet. Validate assumptions first.", "Пока нет. Сначала проверьте предположения на практике."),
        }.get(mode_key, tr("Not enough data to judge yet.", "Данных пока недостаточно."))
        st.write(f"1. {tr('Can this business support ads in theory?', 'Может ли бизнес в теории выдержать рекламу?')} {theory_answer}")
        st.write(f"2. {tr('Is the current data enough to judge?', 'Достаточно ли текущих данных для вывода?')} {data_answer}")
        st.write(f"3. {tr('How much should be spent next to get enough evidence?', 'Сколько потратить дальше, чтобы получить достаточно данных?')} **{next_budget_answer}**")
        st.write(f"4. {tr('If evidence is strong enough, should we scale?', 'Если данных достаточно, стоит ли масштабироваться?')} {scale_answer}")

        if mode_key == "данных_достаточно" and not low_confidence and real_orders > 0 and aov > 0:
            st.divider()
            st.subheader(tr("Scale simulation", "Симуляция масштаба"))
            preset = st.radio(
                tr("How does ad efficiency usually behave when you scale?", "Как обычно меняется эффективность рекламы при росте?"),
                options=["optimistic", "realistic", "pessimistic"],
                format_func=lambda x: {
                    "optimistic": tr("Optimistic", "Оптимистично"),
                    "realistic": tr("Realistic", "Реалистично"),
                    "pessimistic": tr("Pessimistic", "Пессимистично"),
                }[x],
                horizontal=True,
            )
            default_decay = 10 if preset == "optimistic" else 25 if preset == "realistic" else 50
            spend_change_pct = st.slider(tr("Planned ad spend change (%)", "Планируемое изменение бюджета (%)"), -80, 300, 50)
            cac_deterioration_per_100 = st.slider(
                tr("If you double spend, how much can CAC increase (%)?", "Если удвоить бюджет, на сколько может вырасти CAC (%)?"),
                0,
                100,
                default_decay,
            )

            model_revenue = aov * real_orders
            model_cogs = cogs_per_order * real_orders
            res = simulate_scale(
                revenue=model_revenue,
                cogs=model_cogs,
                ad_spend=true_spend,
                orders=real_orders,
                refund_rate_pct=refund_rate_pct,
                spend_change_pct=spend_change_pct,
                cac_deterioration_per_100_pct=cac_deterioration_per_100,
            )
            safe_scale_pct = find_safe_max_scale_pct(
                revenue=model_revenue,
                cogs=model_cogs,
                ad_spend=true_spend,
                orders=real_orders,
                refund_rate_pct=refund_rate_pct,
                cac_deterioration_per_100_pct=cac_deterioration_per_100,
                max_search_pct=300,
            )
            df_curve = build_profit_curve(
                revenue=model_revenue,
                cogs=model_cogs,
                ad_spend=true_spend,
                orders=real_orders,
                refund_rate_pct=refund_rate_pct,
                cac_deterioration_per_100_pct=cac_deterioration_per_100,
            )
            peak_profit, peak_spend, cliff_detected = plot_profit_curve(df_curve)

            s1, s2, s3 = st.columns(3)
            s1.metric(tr("Forecast spend", "Расходы в расчёте"), format_money(res["new_spend"]))
            s2.metric(tr("Forecast profit", "Прибыль в расчёте"), format_money(res["new_profit"]))
            s3.metric(tr("Safe scale limit", "Безопасный лимит роста"), f"{safe_scale_pct}%")

            if cliff_detected:
                st.warning(tr("Profit cliff detected: scaling past the peak reduces profit.", "Обнаружен обрыв прибыли: рост выше пика снижает прибыль."))

            scenarios = [-50, -25, 0, 25, 50, 100, 150, 200]
            rows = []
            for pct in scenarios:
                r = simulate_scale(
                    revenue=model_revenue,
                    cogs=model_cogs,
                    ad_spend=true_spend,
                    orders=real_orders,
                    refund_rate_pct=refund_rate_pct,
                    spend_change_pct=pct,
                    cac_deterioration_per_100_pct=cac_deterioration_per_100,
                )
                rows.append(
                    {
                        tr("Spend change %", "Изменение бюджета, %"): pct,
                        tr("Ad spend", "Расход"): round(r["new_spend"], 2),
                        tr("CAC", "CAC"): round(r["new_cac"], 2) if r["new_cac"] > 0 else None,
                        tr("Orders", "Заказы"): round(r["new_orders"], 1),
                        tr("Revenue", "Выручка"): round(r["new_revenue"], 2),
                        tr("Profit", "Прибыль"): round(r["new_profit"], 2),
                    }
                )
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

st.sidebar.markdown(f"### {tr('Mode summary', 'Сводка режима')}")
if true_spend > 0 or source_key == "новый_бизнес_assumptions_only":
    st.sidebar.write(f"**{tr('Goal', 'Цель')}:** {analysis_goal_map[analysis_goal]}")
    st.sidebar.write(f"**{tr('Source', 'Источник')}:** {dict(source_options)[source_key]}")
    st.sidebar.write(
        f"**{tr('Classified mode', 'Классифицированный режим')}:** "
        f"{tr('New business', 'Новый бизнес') if mode_key == 'новый_бизнес' else tr('Early test', 'Ранний тест') if mode_key == 'ранний_тест' else tr('Validated', 'Подтверждённый режим')}"
    )
    st.sidebar.write(f"**{tr('Confidence', 'Уверенность')}:** {confidence_label}")
    if business_name:
        st.sidebar.write(f"**{tr('Business', 'Бизнес')}:** {business_name}")
else:
    st.sidebar.caption(tr("Fill in your data to see the summary here.", "Заполните данные, чтобы увидеть сводку."))
