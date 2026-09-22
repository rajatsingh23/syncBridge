# SyncBridge Provider Integration Guide

This document explains the provider abstraction used by SyncBridge and describes the Mock Store, Shopify, and WooCommerce integrations.

## Overview

SyncBridge separates provider-specific communication from the core synchronization workflow.

The provider layer is responsible for:

- Communicating with external platforms.
- Fetching products, inventory, and orders.
- Updating inventory where supported.
- Translating provider-specific responses into common schemas.
- Converting HTTP failures into application-level exceptions.

The synchronization layer consumes normalized data rather than depending directly on a provider's response format.

## Provider Architecture

```text
Synchronization Service
          |
          v
   Provider Factory
          |
          v
   Provider Interface
     /      |       \
    /       |        \
 Mock    Shopify   WooCommerce
 Provider Provider  Provider
    |       |        |
    v       v        v
 Mock API  HTTP     HTTP
           Client   Client
             |        |
             v        v
          Adapters / Normalizers
                  |
                  v
         Normalized Schemas
```

## Main Components

### Provider Factory

The provider factory selects a provider implementation based on the store's configured integration.

This prevents synchronization code from containing provider-specific conditionals throughout the application.

Typical flow:

1. Load the store.
2. Read the configured provider.
3. Ask the provider factory for the matching implementation.
4. Execute the requested synchronization operation.

### Base Provider

The base provider defines the common operations expected from provider implementations.

Provider implementations may support operations such as:

- Fetch products.
- Fetch inventory.
- Fetch orders.
- Update inventory.

### HTTP Client

The shared HTTP client wraps outbound HTTP requests.

Default timeouts:

- Connection timeout: 3 seconds
- Read timeout: 10 seconds

The client supports common HTTP methods, including:

- GET
- POST
- PATCH
- PUT
- DELETE

Provider implementations use the HTTP client instead of duplicating low-level request handling.

### Adapters

Adapters translate provider-specific API responses into normalized internal schemas.

This keeps the synchronization service independent of provider-specific field names and response structures.

## Normalized Schemas

The provider layer uses common data structures for synchronization.

Normalized structures include:

- `NormalizedProduct`
- `NormalizedVariant`
- `NormalizedInventory`
- `NormalizedOrder`
- `NormalizedOrderItem`

A normalized object should contain the information required by the synchronization layer without exposing unnecessary provider-specific implementation details.

## Provider Errors

Provider errors are represented by custom exceptions.

Supported exception types include:

- `ProviderError`
- `AuthenticationError`
- `NotFoundError`
- `RateLimitError`
- `TemporaryProviderError`
- `ProviderRequestError`

### Retryable Errors

The synchronization workflow treats temporary failures and rate-limit failures as retryable.

Examples:

- HTTP 429 rate limiting
- HTTP 5xx provider errors
- Temporary network or provider failures

Authentication errors and not-found errors are generally not treated as retryable.

## Mock Provider

The Mock Provider is used for local development, automated testing, and failure simulation.

### Mock Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/mock-store/products/` | Return mock products |
| GET | `/api/mock-store/inventory/` | Return mock inventory |
| GET | `/api/mock-store/orders/` | Return mock orders |
| PATCH | `/api/mock-store/inventory/<external_variant_id>/` | Update mock inventory |

### Failure Simulation

The mock API supports failure query parameters:

```text
?failure=400
?failure=401
?failure=404
?failure=429
?failure=500
```

It also supports simulation parameters:

```text
?simulate=401
?simulate=404
?simulate=429
?simulate=500
?simulate=slow
?simulate=duplicate
```

The available simulations help test:

- Authentication failures
- Missing resources
- Rate limiting
- Temporary server errors
- Slow responses and timeout behavior
- Duplicate data handling

### Example Mock Request

```bash
curl "http://127.0.0.1:8000/api/mock-store/products/"
```

Failure simulation example:

```bash
curl "http://127.0.0.1:8000/api/mock-store/products/?failure=429"
```

## Shopify Provider

The Shopify integration uses Shopify API adapters and the shared HTTP client.

### Supported Operations

- Fetch products.
- Fetch inventory.
- Fetch orders.
- Update inventory where supported by the provider implementation.

### Product Endpoint

The Shopify product adapter uses:

```text
/admin/api/products.json
```

Products and variants are converted into normalized product and variant structures.

### Inventory Endpoint

The Shopify inventory adapter uses:

```text
/admin/api/inventory_levels.json
```

Inventory responses are normalized for use by the synchronization service.

### Orders Endpoint

The Shopify order adapter uses:

```text
/admin/api/orders.json
```

Order records and order items are normalized into the internal order structures.

### Pagination

The Shopify product adapter supports pagination using the provider response's `next` value.

### Currency

The current Shopify adapters use INR as the default currency when normalizing supported data.

### Shopify OAuth

The Shopify integration includes endpoints for starting and handling the OAuth flow:

```text
/api/integrations/shopify/connect
/api/integrations/shopify/callback/
```

The OAuth flow validates the state stored in the session.

The current implementation validates the callback state, while complete access-token persistence and provider onboarding may require additional work.

### Shopify Webhooks

Shopify webhook requests use:

```text
X-Shopify-Hmac-Sha256
X-Shopify-Webhook-Id
X-Shopify-Topic
X-Store-ID
```

The webhook signature is verified using Base64-encoded HMAC-SHA256.

## WooCommerce Provider

The WooCommerce integration uses WooCommerce API endpoints, the shared HTTP client, and provider-specific adapters.

### Supported Operations

- Fetch products.
- Fetch product variations.
- Fetch inventory.
- Fetch orders.
- Update inventory where supported by the provider implementation.

### Products Endpoint

The WooCommerce product adapter uses:

```text
/products
```

### Variations Endpoint

Product variations are fetched using:

```text
/products/{id}/variations
```

### Orders Endpoint

The WooCommerce order adapter uses:

```text
/orders
```

### Pagination

WooCommerce requests use page-based pagination with a `per_page` value.

The implementation uses a page size of 100 where applicable.

### Inventory

WooCommerce inventory synchronization reads stock information from products and variations, including `stock_quantity` where available.

### Orders

WooCommerce order data is normalized into internal order and order-item structures.

The adapter maps provider-specific order statuses, customer details, totals, and dates into the normalized representation.

### WooCommerce Webhooks

WooCommerce webhook requests use:

```text
X-WC-Webhook-Signature
X-WC-Webhook-ID
X-WC-Webhook-Topic
X-Store-ID
```

The webhook signature is verified using HMAC-SHA256.

## Provider Selection

The provider implementation is selected using the store's configured integration provider.

The supported provider values are:

- Mock
- Shopify
- WooCommerce

A store must use the provider expected by the corresponding webhook endpoint. For example, a Shopify webhook cannot be accepted for a store configured with the Mock provider.

## Adding a New Provider

A new provider should follow these steps.

### 1. Define Provider Requirements

Identify the operations needed by the synchronization workflow:

- Product retrieval
- Inventory retrieval
- Order retrieval
- Inventory updates, if required
- Authentication
- Pagination
- Error mapping

### 2. Implement the Provider

Create a provider implementation that follows the base provider contract.

The provider should use the shared HTTP client for outbound requests.

### 3. Implement Adapters

Create provider-specific adapters that convert external API responses into normalized schemas.

Avoid placing provider-specific response parsing directly inside synchronization services.

### 4. Add Provider Factory Support

Register the new provider in the provider factory so the synchronization layer can select it.

### 5. Map Provider Errors

Translate provider HTTP responses into the application's provider exception types.

At minimum, consider:

- Authentication failures
- Missing resources
- Rate limits
- Temporary server failures
- Invalid requests
- Network errors

### 6. Add Tests

Tests should cover:

- Successful product retrieval
- Successful inventory retrieval
- Successful order retrieval
- Pagination
- Provider authentication failures
- Not-found responses
- Rate limiting
- Temporary server errors
- Invalid response data
- Inventory update behavior, if supported

### 7. Add Documentation

Document:

- Required credentials
- API endpoints
- Authentication method
- Pagination behavior
- Supported synchronization operations
- Webhook signature requirements
- Known provider limitations

## Provider Security

Provider credentials and webhook secrets must be handled carefully.

Recommendations:

- Load secrets from environment variables or a secret manager.
- Do not log API keys or webhook secrets.
- Do not expose credentials in API responses.
- Verify webhook signatures before processing events.
- Use HTTPS for external provider communication.
- Apply provider-specific permissions and scopes only when required.

The current store serializer excludes credentials from API responses. Database-field-level encryption for store credentials is not currently implemented.

## Testing Provider Integrations

Run the complete test suite:

```bash
python manage.py test
```

Run Django checks:

```bash
python manage.py check
```

Use the Mock Provider to test provider failures locally before testing against external services.

Recommended scenarios:

1. Successful product synchronization.
2. Successful inventory synchronization.
3. Successful order synchronization.
4. HTTP 401 authentication failure.
5. HTTP 404 missing resource.
6. HTTP 429 rate limiting.
7. HTTP 500 temporary provider failure.
8. Slow response and timeout handling.
9. Duplicate product or webhook event handling.
10. Invalid provider payloads.

## Current Limitations

- Store credentials are stored in a JSON field and are not encrypted at the database-field level.
- The Shopify OAuth callback validates state, but complete token persistence and onboarding require additional work.
- Webhook business processing is currently a placeholder.
- Full synchronization is defined but is not currently implemented by the synchronization runner.
- Provider-specific capabilities may differ depending on the external API.
