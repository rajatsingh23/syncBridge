from dataclasses import dataclass
from decimal import Decimal

@dataclass
class NormalizedVariant:
    external_id: str
    sku: str
    price: Decimal
    currency: str


@dataclass
class NormalizedProduct:
    external_id: str
    title: str
    description: str
    variants: list[NormalizedVariant]

@dataclass
class NormalizedInventory:
    external_variant_id: str
    sku: str
    quantity: int
    reserved_quantity: int

@dataclass
class NormalizedOrder:
    external_id: str
    customer_name: str
    status: str
    total_amount: Decimal
    currency: str