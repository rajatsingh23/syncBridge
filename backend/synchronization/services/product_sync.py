from django.db import transaction

from products.models import (
    ExternalProduct,
    ExternalVariant,
    Product,
    Variant,
)


@transaction.atomic
def sync_product(store, normalized_product):
    external_product = (
        ExternalProduct.objects
        .select_related("product")
        .filter(
            store=store,
            external_id=normalized_product.external_id,
        )
        .first()
    )

    if external_product is None:
        product = Product.objects.create(
            owner=store.user,
            title=normalized_product.title,
            description=normalized_product.description,
        )

        external_product = ExternalProduct.objects.create(
            product=product,
            store=store,
            external_id=normalized_product.external_id,
        )
    else:
        product = external_product.product

    product.title = normalized_product.title
    product.description = normalized_product.description
    product.save(update_fields=["title", "description", "updated_at"])

    for normalized_variant in normalized_product.variants:
        sync_variant(
            store=store,
            product=product,
            normalized_variant=normalized_variant,
        )

    return product


def sync_variant(store, product, normalized_variant):
    external_variant = (
        ExternalVariant.objects
        .select_related("variant")
        .filter(
            store=store,
            external_id=normalized_variant.external_id,
        )
        .first()
    )

    if external_variant is None:
        variant = Variant.objects.create(
            product=product,
            sku=normalized_variant.sku,
            title=normalized_variant.sku,
            price=normalized_variant.price,
            currency=normalized_variant.currency,
        )

        ExternalVariant.objects.create(
            variant=variant,
            store=store,
            external_id=normalized_variant.external_id,
        )
    else:
        variant = external_variant.variant

    variant.product = product
    variant.sku = normalized_variant.sku
    variant.price = normalized_variant.price
    variant.currency = normalized_variant.currency
    variant.save(
        update_fields=[
            "product",
            "sku",
            "price",
            "currency",
            "updated_at",
        ],
    )

    return variant