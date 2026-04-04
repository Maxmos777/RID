"""
Stripe billing helpers.

Origem: RockItDown/src/helpers/billing.py (adaptado).
Melhorias:
  - logging em vez de print()
  - Guard de produção para sk_test
  - Assinaturas keyword-only para evitar erros por posição

Guard de produção
-----------------
Se STRIPE_SECRET_KEY começa com 'sk_test' fora de DEBUG (e sem
STRIPE_TEST_OVERRIDE=True), levanta ValueError imediatamente ao importar.
Esta verificação foi adicionada após incidente no RockItDown onde
a chave de teste foi usada em produção.
"""
from __future__ import annotations

import logging

import stripe
from django.conf import settings

logger = logging.getLogger(__name__)

_key: str = getattr(settings, "STRIPE_SECRET_KEY", "")
_debug: bool = getattr(settings, "DEBUG", False)
_override: bool = getattr(settings, "STRIPE_TEST_OVERRIDE", False)

if _key and _key.startswith("sk_test") and not _debug and not _override:
    raise ValueError(
        "STRIPE_SECRET_KEY é uma chave de teste mas DEBUG=False. "
        "Use uma chave live em produção ou defina STRIPE_TEST_OVERRIDE=True."
    )

stripe.api_key = _key


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def serialize_subscription(sub) -> dict:
    from helpers.utils import timestamp_to_datetime
    return {
        "status": sub.status,
        "current_period_start": timestamp_to_datetime(sub.current_period_start),
        "current_period_end": timestamp_to_datetime(sub.current_period_end),
        "cancel_at_period_end": sub.cancel_at_period_end,
    }


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------

def create_customer(
    *,
    name: str = "",
    email: str = "",
    metadata: dict | None = None,
    raw: bool = False,
):
    resp = stripe.Customer.create(name=name, email=email, metadata=metadata or {})
    logger.info("Stripe customer criado: %s", resp.id)
    return resp if raw else resp.id


# ---------------------------------------------------------------------------
# Products & Prices
# ---------------------------------------------------------------------------

def create_product(
    *,
    name: str = "",
    metadata: dict | None = None,
    raw: bool = False,
):
    resp = stripe.Product.create(name=name, metadata=metadata or {})
    return resp if raw else resp.id


def create_price(
    *,
    currency: str = "usd",
    unit_amount: int = 9999,
    interval: str = "month",
    product: str,
    metadata: dict | None = None,
    raw: bool = False,
):
    resp = stripe.Price.create(
        currency=currency,
        unit_amount=unit_amount,
        recurring={"interval": interval},
        product=product,
        metadata=metadata or {},
    )
    return resp if raw else resp.id


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------

def start_checkout_session(
    customer_id: str,
    *,
    success_url: str,
    cancel_url: str,
    price_stripe_id: str,
    raw: bool = True,
):
    if not success_url.endswith("?session_id={CHECKOUT_SESSION_ID}"):
        success_url += "?session_id={CHECKOUT_SESSION_ID}"
    resp = stripe.checkout.Session.create(
        customer=customer_id,
        success_url=success_url,
        cancel_url=cancel_url,
        line_items=[{"price": price_stripe_id, "quantity": 1}],
        mode="subscription",
    )
    return resp if raw else resp.url


def get_checkout_session(stripe_id: str, *, raw: bool = True):
    resp = stripe.checkout.Session.retrieve(stripe_id)
    return resp if raw else resp.url


def get_checkout_customer_plan(session_id: str) -> dict:
    """Retorna dados consolidados: customer_id, plan_id, sub_stripe_id + subscription_data."""
    checkout = get_checkout_session(session_id, raw=True)
    sub = stripe.Subscription.retrieve(checkout.subscription)
    return {
        "customer_id": checkout.customer,
        "plan_id": sub.plan.id,
        "sub_stripe_id": checkout.subscription,
        **serialize_subscription(sub),
    }


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------

def get_subscription(stripe_id: str, *, raw: bool = True):
    resp = stripe.Subscription.retrieve(stripe_id)
    return resp if raw else serialize_subscription(resp)


def get_customer_active_subscriptions(customer_stripe_id: str):
    return stripe.Subscription.list(customer=customer_stripe_id, status="active")


def cancel_subscription(
    stripe_id: str,
    *,
    reason: str = "",
    feedback: str = "other",
    cancel_at_period_end: bool = False,
    raw: bool = True,
):
    details = {"comment": reason, "feedback": feedback}
    if cancel_at_period_end:
        resp = stripe.Subscription.modify(
            stripe_id,
            cancel_at_period_end=True,
            cancellation_details=details,
        )
    else:
        resp = stripe.Subscription.cancel(stripe_id, cancellation_details=details)
    logger.info("Subscrição %s cancelada (at_period_end=%s)", stripe_id, cancel_at_period_end)
    return resp if raw else serialize_subscription(resp)
