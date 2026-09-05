from django.db import migrations


def create_integrations(apps, schema_editor):
    Integration = apps.get_model("stores", "Integration")

    Integration.objects.bulk_create(
        [
            Integration(
                name="Mock Store",
                provider="mock",
            ),
            Integration(
                name="Shopify",
                provider="shopify",
            ),
            Integration(
                name="WooCommerce",
                provider="woocommerce",
            ),
        ]
    )


def delete_integrations(apps, schema_editor):
    Integration = apps.get_model("stores", "Integration")

    Integration.objects.filter(
        provider__in=["mock", "shopify", "woocommerce"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("stores", "0002_store"),
    ]

    operations = [
        migrations.RunPython(
            create_integrations,
            delete_integrations,
        ),
    ]