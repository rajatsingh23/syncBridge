# Synchronization

## Overview

SyncBridge synchronizes catalog, inventory, and order data between the application and external commerce providers.

The synchronization layer uses:

- `SyncJob` to track a synchronization run.
- Provider adapters to retrieve normalized external data.
- External mapping models to connect provider IDs with internal records.
- Django transactions to keep related updates consistent.
- Celery for background execution and retry handling.
- `SyncError` to record entity-level failures.

## Sync Job Types

The supported synchronization types are:

- `products` — synchronizes products and variants.
- `inventory` — synchronizes inventory quantities.
- `orders` — synchronizes orders and order items.
- `full` — intended for a complete synchronization, but currently unsupported by the execution logic.

The `full` type is currently defined but raises a `ValueError` when execution is attempted. It should not be presented as a working synchronization mode yet.

## Sync Job Lifecycle

A sync job tracks its progress through these statuses:

- `pending` — created but not started.
- `running` — currently being processed.
- `completed` — finished successfully.
- `partial` — completed with some failures.
- `failed` — execution failed.
- `cancelled` — stopped before completion.

The job records progress using fields such as:

- `total_items`
- `processed_items`
- `successful_items`
- `failed_items`
- `started_at`
- `completed_at`
- `errors`

The serializer exposes job information as read-only data. The current API does not document a dedicated endpoint for creating or starting a synchronization job.

## Product Synchronization

Product synchronization processes normalized products returned by a provider.

The general flow is:

1. Select the store and its configured provider.
2. Retrieve normalized products from the provider adapter.
3. Find or create the corresponding product using the external product mapping.
4. Update product information.
5. Create or update related variants.
6. Save external product and variant mappings.
7. Track progress and errors in the sync job.

Product synchronization uses external IDs to avoid creating duplicate internal records for the same provider entity.

Product and variant updates are performed transactionally so related changes can be committed consistently.

## Inventory Synchronization

Inventory synchronization updates inventory quantities for mapped variants.

The general flow is:

1. Retrieve normalized inventory data from the provider.
2. Find the internal variant using the external variant mapping.
3. Create or update the inventory record.
4. Update synchronization progress.
5. Record failures when an item cannot be processed.

Inventory synchronization requires an existing external variant mapping. If a mapping is missing, the synchronization logic raises a `ValueError` rather than guessing which internal variant should be updated.

## Order Synchronization

Order synchronization imports normalized orders and their items.

The general flow is:

1. Retrieve normalized orders from the provider.
2. Map the external order status to the internal order status.
3. Create or update the internal order using the external order identifier.
4. Process each order item.
5. Resolve the related internal variant through its external mapping.
6. Create or update order-item records.
7. Track successes and failures.

If an order item references a variant for which no external mapping exists, the synchronization logic raises a `ValueError`.

## External ID Mappings

External mappings connect provider-specific identifiers to internal SyncBridge records.

Mappings are scoped to a store, which prevents an external ID belonging to one store from being treated as the same entity for another store.

Mappings are important because provider identifiers are not guaranteed to match internal database IDs.

The synchronization process uses mappings to:

- Prevent duplicate products and variants.
- Resolve inventory records to internal variants.
- Connect order items to internal variants.
- Support repeated synchronization runs.

## Provider Normalization

Provider adapters convert provider-specific responses into normalized structures.

The synchronization layer uses normalized data classes including:

- `NormalizedProduct`
- `NormalizedVariant`
- `NormalizedInventory`
- `NormalizedOrder`
- `NormalizedOrderItem`

This keeps synchronization logic independent of the response format used by Shopify, WooCommerce, or the mock provider.

The provider factory currently supports:

- `mock`
- `shopify`
- `woocommerce`

## Celery Background Tasks

Synchronization can run through Celery.

The worker can be started locally with:

```bash
celery -A config worker --loglevel=INFO --pool=solo
```

The `run_sync_task` Celery task supports retry handling:

- Maximum retries: `3`
- Retry delay: `2` seconds
- Retries occur when an exception is marked as retryable.
- Non-retryable errors are not automatically retried by this task.

Celery uses the configured Redis URL as its broker and result backend.

## Error Tracking

Entity-level synchronization errors are represented by `SyncError`.

Relevant fields include:

- `entity_type`
- `entity_id`
- `error_type`
- `status_code`
- `message`
- `retry_count`
- `resolved`
- `created_at`

These fields provide context about what failed, the type of failure, whether an HTTP status was involved, and whether the error has been resolved.

Errors should be recorded with enough context to support debugging without exposing secrets or provider credentials.

## Transaction Handling

Synchronization logic uses database transactions for related updates, especially when products and their variants are processed together.

Transactions help prevent partially committed changes when a related operation fails.

However, transactions do not guarantee that every external provider operation can be rolled back. External API calls and local database changes should therefore be treated as separate systems.

## Retry Behavior

Retry behavior is implemented at the Celery task level.

A retry is appropriate for temporary or recoverable failures, such as some provider or network errors. Permanent data problems, such as missing external mappings, should generally be investigated rather than repeatedly retried.

The current task configuration retries retryable exceptions up to three times with a two-second countdown.

## Current Limitations

The current synchronization implementation has these limitations:

- The `full` synchronization type is defined but not implemented.
- The current API documentation does not expose a dedicated job-creation or job-start endpoint.
- Provider credentials are still stored in a JSON field rather than an encrypted database field.
- Synchronization behavior depends on external mappings being present.
- External provider operations cannot be rolled back by local database transactions.
- Production-scale worker deployment, scheduling, and observability require additional configuration.
- Webhook receipt and signature validation are separate from the full synchronization workflow.

## Useful Commands

Run Django checks:

```bash
python manage.py check
```

Run tests:

```bash
python manage.py test
```

Start the Celery worker:

```bash
celery -A config worker --loglevel=INFO --pool=solo
```

Start the Django development server:

```bash
python manage.py runserver
```

## Summary

SyncBridge separates provider-specific integration code from internal synchronization logic by using normalized data structures and external ID mappings.

The current implementation supports product, inventory, and order synchronization paths, with Celery-based execution and retry handling. The `full` synchronization mode and a documented public trigger endpoint remain unfinished.
