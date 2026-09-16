from products.models import ExternalVariant, Inventory


def sync_inventory(store, normalized_inventory):
    external_variant = (
        ExternalVariant.objects
        .select_related("variant")
        .filter(
            store=store,
            external_id=normalized_inventory.external_variant_id,
        )
        .first()
    )

    if external_variant is None:
        raise ValueError(
            "External variant mapping not found: "
            f"{normalized_inventory.external_variant_id}"
        )

    inventory, created = Inventory.objects.update_or_create(
        variant=external_variant.variant,
        store=store,
        defaults={
            "quantity": normalized_inventory.quantity,
            "reserved_quantity": normalized_inventory.reserved_quantity,
        },
    )

    return inventory