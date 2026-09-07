from dataclasses import dataclass


@dataclass
class NormalizedVariant:
    external_id: str
    sku: str
    price: str
    currency: str


@dataclass
class NormalizedProduct:
    external_id: str
    title: str
    description: str
    variants: list[NormalizedVariant]