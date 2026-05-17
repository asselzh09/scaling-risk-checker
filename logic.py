import re

import pandas as pd


def safe_div(a, b):
    return a / b if b not in [0, 0.0, None] else 0.0


def format_money(v, currency_symbol="$"):
    if v is None:
        return "n/a"
    try:
        return f"{currency_symbol}{float(v):,.2f}"
    except (TypeError, ValueError):
        return "n/a"


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


def get_data_quality_note(meta_convos, ad_spend, close_rate, aov, lang):
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


# ---------------------------------------------------------------------------
# Phase 1 — input plausibility checks
# Gentle, benchmark-based warnings for values a user is likely unsure about.
# Returns a single localized string, or None if the value looks fine.
# ---------------------------------------------------------------------------
def plausibility_note(field, value, lang, aov=0.0):
    def tr(en, ru):
        return en if lang == "English" else ru

    try:
        value = float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return None
    try:
        aov = float(aov) if aov is not None else 0.0
    except (TypeError, ValueError):
        aov = 0.0

    if field == "close_rate":
        if value <= 0:
            return None
        if value > 0.6:
            return tr(
                f"{value:.0%} is unusually high for conversation-to-order. "
                "Make sure this is paid orders divided by meaningful conversations — "
                "not clicks or add-to-carts.",
                f"{value:.0%} — необычно высокая конверсия из обращения в заказ. "
                "Убедитесь, что это оплаченные заказы, делённые на осмысленные обращения, "
                "а не клики или корзины.",
            )
        if value < 0.03:
            return tr(
                f"{value:.0%} is very low. If that is real, paid acquisition will be "
                "expensive — check that junk or bot chats are not inflating the "
                "conversation count.",
                f"{value:.0%} — очень низкая конверсия. Если это так, платное привлечение "
                "будет дорогим — проверьте, что мусорные или бот-диалоги не завышают "
                "число обращений.",
            )
        return None

    if field == "refund_rate_pct":
        if value <= 0:
            return None
        if value > 30:
            return tr(
                f"{value:.0f}% returns is very high. Confirm this is the share of "
                "orders refunded, not a count.",
                f"{value:.0f}% возвратов — это очень много. Убедитесь, что это доля "
                "возвращённых заказов, а не их количество.",
            )
        return None

    if field == "cogs_per_order":
        if value <= 0 or aov <= 0:
            return None
        if value >= aov:
            return tr(
                "Product cost is at or above the order value — there is no margin "
                "left for ads or profit. Double-check both numbers.",
                "Себестоимость не ниже среднего чека — на рекламу и прибыль не "
                "остаётся ничего. Перепроверьте обе цифры.",
            )
        if value / aov > 0.8:
            return tr(
                f"Product cost is {value / aov:.0%} of the order value — very little "
                "room left for ad spend.",
                f"Себестоимость составляет {value / aov:.0%} от среднего чека — "
                "на рекламу почти не остаётся места.",
            )
        return None

    return None


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
    ad_impact = profit_before_ads - baseline_profit

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
        "Средний чек": aov,
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


def get_status(res, t):
    if res["baseline_profit"] < 0 or res["break_even_cac"] <= 0 or res["new_profit"] < 0:
        return t["status_hold"], "hold"
    if res["new_risk_ratio"] > 0.80:
        return t["status_fragile"], "fragile"
    return t["status_safe"], "safe"


def get_bottleneck(aov, cogs_per_order, cac, break_even_cac, refund_rate, t):
    if break_even_cac <= 0:
        return t["bottleneck_neg"]
    if cac > break_even_cac:
        return t["bottleneck_cac"]
    if refund_rate > 10:
        return t["bottleneck_ref"]
    if aov > 0 and ((aov - cogs_per_order) / aov) < 0.35:
        return t["bottleneck_margin"]
    return t["bottleneck_ok"]


def get_recommendation(res, refund_rate, t):
    aov = res["Средний чек"]
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
    baseline = simulate_scale(
        revenue=revenue,
        cogs=cogs,
        ad_spend=ad_spend,
        orders=orders,
        refund_rate_pct=refund_rate_pct,
        spend_change_pct=0,
        cac_deterioration_per_100_pct=cac_deterioration_per_100_pct,
    )
    if baseline["new_profit"] < 0:
        return 0

    last_safe = 0
    for pct in range(1, max_search_pct + 1):
        r = simulate_scale(
            revenue=revenue,
            cogs=cogs,
            ad_spend=ad_spend,
            orders=orders,
            refund_rate_pct=refund_rate_pct,
            spend_change_pct=pct,
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


def profit_flag(p, baseline_revenue):
    if p < 0:
        return "🔴"
    if baseline_revenue > 0 and p < baseline_revenue * 0.05:
        return "🟠"
    return "🟢"


def get_ads_verdict(res, t):
    if res["baseline_profit"] < 0 and res["profit_before_ads"] > 0:
        return t["ads_destroying"]
    if res["baseline_profit"] > 0 and res["margin_buffer"] > 0 and res["risk_ratio"] < 0.7:
        return t["ads_ok"]
    if res["baseline_profit"] > 0 and res["margin_buffer"] > 0:
        return t["ads_weak"]
    return t["ads_not_problem"]


def get_best_next_move(res, refund_rate, peak_spend, current_spend, t):
    aov = res["Средний чек"]
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


def _tr(lang, en, ru):
    return en if lang == "English" else ru


def evaluate_decision_state(
    source_key,
    used_conversations,
    real_orders,
    threshold,
    spend_is_adjusted,
    has_economics,
    lead_quality,
    true_spend,
    close_rate_source,
    lang,
):
    reasons = []

    def tr(en, ru):
        return en if lang == "English" else ru

    if source_key == "новый_бизнес_assumptions_only":
        reasons.append(tr("assumptions only", "только предположения"))
        return {
            "mode_key": "новый_бизнес",
            "confidence_label": tr("Low", "Низкая"),
            "confidence_reasons": reasons,
            "low_confidence": True,
        }

    if used_conversations < threshold:
        reasons.append(tr("low real conversation volume", "мало реальных обращений"))
    if real_orders <= 0:
        reasons.append(tr("no real orders yet", "ещё нет реальных заказов"))
    if not has_economics:
        reasons.append(tr("economics incomplete", "экономика заполнена не полностью"))
    if spend_is_adjusted:
        reasons.append(tr("spend adjusted manually", "расход скорректирован вручную"))
    if lead_quality == "weak":
        reasons.append(tr("lead quality is weak", "качество обращений слабое"))
    if close_rate_source == "guess":
        reasons.append(tr("close rate is guessed", "конверсия в покупку указана как предположение"))

    enough_real_data = (
        used_conversations >= threshold
        and real_orders >= 3
        and has_economics
        and true_spend > 0
    )

    high_confidence = (
        enough_real_data
        and not spend_is_adjusted
        and lead_quality != "weak"
    )

    if high_confidence:
        return {
            "mode_key": "данных_достаточно",
            "confidence_label": tr("High", "Высокая"),
            "confidence_reasons": reasons or [tr("real orders and enough downstream data", "есть реальные заказы и достаточно данных")],
            "low_confidence": False,
        }

    if enough_real_data:
        return {
            "mode_key": "данных_достаточно",
            "confidence_label": tr("Medium", "Средняя"),
            "confidence_reasons": reasons,
            "low_confidence": False,
        }

    some_evidence_exists = (
        used_conversations > 0
        or real_orders > 0
        or has_economics
    )

    if some_evidence_exists:
        return {
            "mode_key": "ранний_тест",
            "confidence_label": tr("Medium", "Средняя"),
            "confidence_reasons": reasons,
            "low_confidence": True,
        }

    return {
        "mode_key": "ранний_тест",
        "confidence_label": tr("Low", "Низкая"),
        "confidence_reasons": reasons,
        "low_confidence": True,
    }


def classify_mode_v2(source_key, used_conversations, real_orders, threshold, close_rate_confidence, close_rate_source, has_economics, true_spend):
    state = evaluate_decision_state(
        source_key=source_key,
        used_conversations=used_conversations,
        real_orders=real_orders,
        threshold=threshold,
        spend_is_adjusted=False,
        has_economics=has_economics,
        lead_quality="mixed",
        true_spend=true_spend,
        close_rate_source=close_rate_source,
        lang="Русский",
    )
    return state["mode_key"]


def is_low_confidence_v2(source_key, mode_key, real_orders, close_rate_source, used_conversations, threshold):
    state = evaluate_decision_state(
        source_key=source_key,
        used_conversations=used_conversations,
        real_orders=real_orders,
        threshold=threshold,
        spend_is_adjusted=False,
        has_economics=used_conversations > 0 or real_orders > 0,
        lead_quality="mixed",
        true_spend=0,
        close_rate_source=close_rate_source,
        lang="Русский",
    )
    return state["low_confidence"]


def get_confidence_v2(source_key, used_conversations, real_orders, threshold, close_rate_source, spend_is_adjusted, has_economics, lead_quality, lang):
    state = evaluate_decision_state(
        source_key=source_key,
        used_conversations=used_conversations,
        real_orders=real_orders,
        threshold=threshold,
        spend_is_adjusted=spend_is_adjusted,
        has_economics=has_economics,
        lead_quality=lead_quality,
        true_spend=0,
        close_rate_source=close_rate_source,
        lang=lang,
    )
    return state["confidence_label"], state["confidence_reasons"]


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
    lang,
    currency_symbol,
):
    if mode_key == "новый_бизнес":
        headline = _tr(lang, "Scenario planning only", "Только предварительный расчёт")
        body = [
            _tr(lang, "Use this as a validation plan, not a profit promise.", "Используйте это как план проверки, а не как обещание прибыли."),
            _tr(
                lang,
                f"Target CAC: {format_money(max(target_cac, 0.0), currency_symbol)}",
                f"Целевая стоимость привлечения клиента: {format_money(max(target_cac, 0.0), currency_symbol)}",
            ),
            _tr(
                lang,
                f"Validation budget for {int(target_conversations)} conversations: {format_money(recommended_test_budget, currency_symbol)}",
                f"Бюджет на проверку для {int(target_conversations)} обращений: {format_money(recommended_test_budget, currency_symbol)}",
            ),
        ]
        return headline, body

    if mode_key == "ранний_тест":
        # Low-confidence mode: hold back. Give context, not a spend recommendation.
        headline = _tr(lang, "Not enough data yet — keep testing", "Данных пока недостаточно — продолжайте тест")
        track_metric = (
            _tr(lang, "actual paid spend and real conversations", "фактически оплаченный расход и реальные диалоги")
            if real_orders <= 0
            else _tr(lang, "qualified leads, first orders, and refunds", "квалифицированные обращения, первые заказы и возвраты")
        )
        caution = _tr(
            lang,
            "There is not enough evidence here to recommend a spend level. Treat the numbers below as context, not advice.",
            "Здесь недостаточно данных, чтобы рекомендовать уровень бюджета. Считайте цифры ниже контекстом, а не рекомендацией.",
        )
        cpc_line = _tr(
            lang,
            f"Current cost per conversation: {format_money(cost_per_conversation, currency_symbol)}",
            f"Текущая стоимость обращения: {format_money(cost_per_conversation, currency_symbol)}",
        )
        target_cpc_line = _tr(
            lang,
            f"Target max cost per conversation: {format_money(max_cost_per_conversation, currency_symbol)}",
            f"Целевая максимальная стоимость обращения: {format_money(max_cost_per_conversation, currency_symbol)}",
        )
        budget_line = _tr(
            lang,
            f"Rough planning figure only — collecting {int(target_conversations)} conversations at today's cost "
            f"would take about {format_money(recommended_test_budget, currency_symbol)}. This is not a spend recommendation.",
            f"Только ориентир для планирования — чтобы собрать {int(target_conversations)} обращений по текущей цене, "
            f"потребуется примерно {format_money(recommended_test_budget, currency_symbol)}. Это не рекомендация по бюджету.",
        )
        if max_cost_per_conversation > 0 and cost_per_conversation > max_cost_per_conversation * 1.15:
            signal_line = _tr(
                lang,
                f"The current signal looks expensive even for testing. Track {track_metric} next.",
                f"Текущий сигнал выглядит дорогим даже для теста. Дальше отслеживайте {track_metric}.",
            )
        elif max_cost_per_conversation > 0 and cost_per_conversation > max_cost_per_conversation:
            signal_line = _tr(
                lang,
                f"The current signal is borderline. Collect more evidence carefully and track {track_metric} next.",
                f"Текущие цифры пограничные. Аккуратно соберите больше данных и дальше отслеживайте {track_metric}.",
            )
        else:
            signal_line = _tr(
                lang,
                f"The current signal may be workable, but there is not enough evidence yet. Track {track_metric} next.",
                f"Текущие цифры могут быть рабочими, но данных пока недостаточно. Дальше отслеживайте {track_metric}.",
            )
        body = [caution, cpc_line, target_cpc_line, signal_line, budget_line]
        return headline, body

    # Phase 4: evidence-backed recommendations. Each branch shows the number(s)
    # and threshold that triggered it, so the user can see WHY — not just WHAT.
    refund_order_rate = safe_div(refund_count, real_orders) if real_orders > 0 else 0.0
    if refund_order_rate >= 0.10 or (refund_count >= 3 and refund_order_rate >= 0.05):
        return _tr(lang, "Fix refunds first", "Сначала разберитесь с возвратами"), [
            _tr(
                lang,
                f"Refunds are {refund_order_rate:.1%} of orders ({int(refund_count)} of "
                f"{int(real_orders)}), above the 10% threshold where they materially "
                f"reduce safe CAC. Fix this before scaling spend.",
                f"Возвраты составляют {refund_order_rate:.1%} от заказов ({int(refund_count)} "
                f"из {int(real_orders)}), выше порога 10%, при котором они заметно снижают "
                f"безопасный CAC. Решите это до роста бюджета.",
            ),
        ]
    if lead_quality == "weak":
        return _tr(lang, "Improve lead quality", "Улучшите качество обращений"), [
            _tr(lang,
                "You marked lead quality as 'weak' — cheap conversations that don't convert "
                "make CAC look better than it really is. Tighten the audience or creative first.",
                "Вы отметили качество обращений как «слабое» — дешёвые диалоги, которые не "
                "конвертируются, занижают видимый CAC. Сначала сузьте аудиторию или поправьте креатив."),
        ]
    if break_even_cac <= 0:
        return _tr(lang, "Improve margin first", "Сначала увеличьте прибыль с заказа"), [
            _tr(lang,
                f"Break-even CAC is {format_money(break_even_cac, currency_symbol)} — your "
                f"first-order economics can't support any paid acquisition. Raise AOV or cut "
                f"product cost before touching ad spend.",
                f"Точка безубытка CAC = {format_money(break_even_cac, currency_symbol)} — "
                f"экономика первого заказа не поддерживает платное привлечение. Сначала повысьте "
                f"средний чек или снизьте себестоимость, и только потом — рекламу."),
        ]
    if real_cac and target_cac > 0 and real_cac <= target_cac * 0.85:
        _gap_pct = (1 - real_cac / target_cac) * 100
        return _tr(lang, "Scale gradually", "Увеличивайте бюджет постепенно"), [
            _tr(lang,
                f"Real CAC {format_money(real_cac, currency_symbol)} is {_gap_pct:.0f}% "
                f"below target CAC {format_money(target_cac, currency_symbol)} — you have "
                f"room to scale carefully. Watch whether CAC stays under target as spend rises.",
                f"Реальный CAC {format_money(real_cac, currency_symbol)} на {_gap_pct:.0f}% "
                f"ниже целевого {format_money(target_cac, currency_symbol)} — есть запас для "
                f"осторожного роста. Следите, чтобы CAC не превысил целевой при росте бюджета."),
        ]
    if real_cac and break_even_cac > 0 and real_cac > break_even_cac:
        _over_pct = (real_cac / break_even_cac - 1) * 100
        return _tr(lang, "Reduce spend", "Снизьте бюджет"), [
            _tr(lang,
                f"Real CAC {format_money(real_cac, currency_symbol)} is {_over_pct:.0f}% "
                f"above break-even {format_money(break_even_cac, currency_symbol)} — current "
                f"growth is destroying profit on every new customer.",
                f"Реальный CAC {format_money(real_cac, currency_symbol)} на {_over_pct:.0f}% "
                f"выше уровня безубытка {format_money(break_even_cac, currency_symbol)} — "
                f"текущий рост уничтожает прибыль на каждом новом клиенте."),
        ]
    if real_cac and target_cac > 0 and break_even_cac > 0:
        return _tr(lang, "Hold current spend", "Оставьте текущий бюджет"), [
            _tr(lang,
                f"Real CAC {format_money(real_cac, currency_symbol)} sits between target "
                f"({format_money(target_cac, currency_symbol)}) and break-even "
                f"({format_money(break_even_cac, currency_symbol)}) — profitable but no "
                f"safety margin. Keep collecting data or improve conversion before pushing spend.",
                f"Реальный CAC {format_money(real_cac, currency_symbol)} между целевым "
                f"({format_money(target_cac, currency_symbol)}) и безубытком "
                f"({format_money(break_even_cac, currency_symbol)}) — прибыль есть, но без "
                f"запаса. Сначала соберите больше данных или улучшите продажи."),
        ]
    return _tr(lang, "Hold current spend", "Оставьте текущий бюджет"), [
        _tr(lang, "Keep collecting data or improve conversion before scaling harder.",
            "Продолжайте собирать данные или сначала улучшите продажи."),
    ]
