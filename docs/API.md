# SyncBridge API Reference

This document describes the main API endpoints exposed by SyncBridge.

## Base URL

Local development:

```text
http://127.0.0.1:8000
```

All API endpoints use the `/api/` prefix.

## Authentication

SyncBridge uses JWT authentication.

### Obtain Tokens

```http
POST /api/auth/token/
Content-Type: application/json
```

Request:

```json
{
  "email": "user@example.com",
  "password": "your-password"
}
```

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your-password"
  }'
```

The response contains an access token and a refresh token.

### Refresh Access Token

```http
POST /api/auth/token/refresh/
Content-Type: application/json
```

Request:

```json
{
  "refresh": "YOUR_REFRESH_TOKEN"
}
```

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

### Get Current User

```http
GET /api/auth/me/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Example:

```bash
curl http://127.0.0.1:8000/api/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Unauthenticated requests return:

```json
{
  "detail": "Authentication credentials were not provided."
}
```

## Authentication Requirements

Unless explicitly mentioned otherwise, API endpoints require:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Users can only access resources associated with their own account.

---

## Stores

Base endpoint:

```text
/api/stores/
```

### List Stores

```http
GET /api/stores/
```

Example:

```bash
curl http://127.0.0.1:8000/api/stores/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create Store

```http
POST /api/stores/
Content-Type: application/json
```

Example request:

```json
{
  "name": "My Mock Store",
  "integration": 1,
  "external_store_id": "mock-store-001",
  "status": "active"
}
```

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/stores/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Mock Store",
    "integration": 1,
    "external_store_id": "mock-store-001",
    "status": "active"
  }'
```

Replace the integration ID and other values with valid records from your database.

### Retrieve Store

```http
GET /api/stores/<id>/
```

### Update Store

```http
PATCH /api/stores/<id>/
Content-Type: application/json
```

### Delete Store

```http
DELETE /api/stores/<id>/
```

Store credentials are not exposed through the store serializer.

---

## Products

Base endpoint:

```text
/api/products/
```

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/products/` | List products |
| POST | `/api/products/` | Create a product |
| GET | `/api/products/<id>/` | Retrieve a product |
| PATCH | `/api/products/<id>/` | Update a product |
| DELETE | `/api/products/<id>/` | Delete a product |

Products are filtered by the authenticated user's ownership.

---

## Variants

Base endpoint:

```text
/api/variants/
```

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/variants/` | List variants |
| POST | `/api/variants/` | Create a variant |
| GET | `/api/variants/<id>/` | Retrieve a variant |
| PATCH | `/api/variants/<id>/` | Update a variant |
| DELETE | `/api/variants/<id>/` | Delete a variant |

A variant must belong to a product owned by the authenticated user.

---

## Inventory

Base endpoint:

```text
/api/inventory/
```

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/inventory/` | List inventory records |
| POST | `/api/inventory/` | Create an inventory record |
| GET | `/api/inventory/<id>/` | Retrieve an inventory record |
| PATCH | `/api/inventory/<id>/` | Update an inventory record |
| DELETE | `/api/inventory/<id>/` | Delete an inventory record |

Inventory access is restricted based on product and store ownership.

---

## External Mappings

### External Products

```text
/api/external-products/
```

| Method | Endpoint |
|---|---|
| GET | `/api/external-products/` |
| POST | `/api/external-products/` |
| GET | `/api/external-products/<id>/` |
| PATCH | `/api/external-products/<id>/` |
| DELETE | `/api/external-products/<id>/` |

### External Variants

```text
/api/external-variants/
```

| Method | Endpoint |
|---|---|
| GET | `/api/external-variants/` |
| POST | `/api/external-variants/` |
| GET | `/api/external-variants/<id>/` |
| PATCH | `/api/external-variants/<id>/` |
| DELETE | `/api/external-variants/<id>/` |

External mappings are validated against the related product and store ownership.

---

## Synchronization Jobs

Base endpoint:

```text
/api/sync/jobs/
```

Sync job endpoints are read-only.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/sync/jobs/` | List sync jobs |
| GET | `/api/sync/jobs/<id>/` | Retrieve a sync job |

Example:

```bash
curl http://127.0.0.1:8000/api/sync/jobs/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Sync job responses can include:

- Sync type
- Status
- Total items
- Processed items
- Successful items
- Failed items
- Start and completion timestamps
- Synchronization errors

Users can only view sync jobs belonging to their own stores.

---

## Shopify OAuth

### Start OAuth

```http
GET /api/integrations/shopify/connect?shop=example.myshopify.com
```

Example:

```bash
curl -i "http://127.0.0.1:8000/api/integrations/shopify/connect?shop=example.myshopify.com"
```

The `shop` parameter must use the `.myshopify.com` domain.

### OAuth Callback

```http
GET /api/integrations/shopify/callback/
```

The callback validates the OAuth state stored in the session.

---

## Webhooks

Webhook endpoints do not use JWT authentication. They use provider-specific signature verification.

### Mock Webhook

```http
POST /api/webhooks/mock/
```

Required headers:

```text
X-Store-ID
X-Webhook-Signature
```

The JSON body must include:

```json
{
  "event_id": "event-001",
  "event_type": "product.created"
}
```

### Shopify Webhook

```http
POST /api/webhooks/shopify/
```

Required headers:

```text
X-Store-ID
X-Shopify-Hmac-Sha256
X-Shopify-Webhook-Id
X-Shopify-Topic
```

### WooCommerce Webhook

```http
POST /api/webhooks/woocommerce/
```

Required headers:

```text
X-Store-ID
X-WC-Webhook-Signature
X-WC-Webhook-ID
X-WC-Webhook-Topic
```

### Webhook Processing

Webhook requests are:

1. Validated.
2. Authenticated using a signature.
3. Checked for duplicate event IDs.
4. Stored in the database.
5. Dispatched to a Celery task after the transaction commits.

Duplicate webhook events return HTTP 200 with a message indicating that the event was already received.

---

## Common HTTP Responses

| Status | Meaning |
|---|---|
| 200 | Request successful |
| 201 | Resource created |
| 400 | Invalid request |
| 401 | Authentication failed or missing |
| 403 | Permission denied |
| 404 | Resource not found |
| 500 | Internal server error |

## Security Notes

- Use JWT access tokens for authenticated API requests.
- Never expose access tokens or provider credentials.
- Do not commit `.env` files.
- Store-level ownership checks are applied to protected resources.
- Webhook signatures must be validated before processing events.
- Django CSRF middleware remains enabled.
- Secrets should be loaded from environment variables.
