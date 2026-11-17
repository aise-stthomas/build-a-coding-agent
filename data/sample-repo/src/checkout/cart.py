"""A cart and its total. Money is in cents, as int."""
from dataclasses import dataclass

TAX_RATE = 0.07


@dataclass
class Item:
    sku: str
    price_cents: int
    qty: int = 1


def subtotal(items):
    return sum(i.price_cents * i.qty for i in items)


def tax(items):
    return subtotal(items) * TAX_RATE


def total(items):
    return subtotal(items) + tax(items)
