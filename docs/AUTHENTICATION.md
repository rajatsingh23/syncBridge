# SyncBridge Authentication Guide

This document explains authentication in SyncBridge, including JWT tokens, protected endpoints, refresh-token rotation, and security testing.

## Overview

SyncBridge uses:

- Django REST Framework
- `djangorestframework-simplejwt`
- Access tokens for authenticated API requests
- Refresh tokens for obtaining new access tokens
- Refresh-token rotation
- Refresh-token blacklisting

Authentication is applied to protected API endpoints, while webhook endpoints use provider-specific signature verification instead of JWT authentication.

## Authentication Flow

```text
Client
  |
  | 1. Submit email and password
  v
POST /api/auth/token/
  |
  | 2. Receive access token + refresh token
  v
Client stores tokens securely
  |
  | 3. Send access token with API requests
  v
Protected API endpoint
  |
  | 4. Access token expires
  v
POST /api/auth/token/refresh/
  |
  | 5. Receive a new access token
  v
Client continues making authenticated requests
```

## Token Types

### Access Token

The access token is sent with requests to protected API endpoints.

Example:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

The configured access-token lifetime is:

```text
30 minutes
```

Access tokens should be treated as sensitive credentials. Do not commit them to source control or expose them in logs.

### Refresh Token

The refresh token is used to obtain a new access token after the access token expires.

The configured refresh-token lifetime is:

```text
7 days
```

Refresh tokens should be stored securely and should not be shared with clients or services that do not need them.

## Obtain Tokens

Endpoint:

```http
POST /api/auth/token/
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

A successful response contains:

```json
{
  "refresh": "YOUR_REFRESH_TOKEN",
  "access": "YOUR_ACCESS_TOKEN"
}
```

The exact response also depends on the configured SimpleJWT serializer and authentication settings.

## Use an Access Token

Protected endpoints require the access token in the `Authorization` header.

Example:

```bash
curl http://127.0.0.1:8000/api/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Example successful response:

```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "Rajat"
}
```

The response fields are based on the current `MeView` implementation.

## Missing or Invalid Authentication

A request without an access token is rejected.

Example:

```bash
curl -i http://127.0.0.1:8000/api/auth/me/
```

Typical response:

```http
HTTP/1.1 401 Unauthorized
```

```json
{
  "detail": "Authentication credentials were not provided."
}
```

An invalid, expired, or malformed access token should also be rejected with an authentication error.

## Refresh an Access Token

Endpoint:

```http
POST /api/auth/token/refresh/
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

Use the returned access token for subsequent protected requests.

## Refresh Token Rotation

SyncBridge is configured with:

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}
```

### Rotation Behavior

When a refresh token is used:

1. The refresh token is validated.
2. A new access token is generated.
3. A new refresh token is generated when rotation is enabled.
4. The previous refresh token is blacklisted when blacklist-after-rotation is enabled.
5. The client should replace the old refresh token with the new one.

The client must not continue using a refresh token that has already been rotated and blacklisted.

## Refresh Token Blacklisting

The SimpleJWT blacklist application is enabled in Django:

```python
"rest_framework_simplejwt.token_blacklist"
```

Database migrations for the token blacklist application must be applied:

```bash
python manage.py migrate
```

To inspect the migration state:

```bash
python manage.py showmigrations token_blacklist
```

The refresh-token rotation and blacklist behavior are covered by automated tests.

## Protected Resources

The following resources use authenticated access and ownership filtering:

- Stores
- Products
- Variants
- Inventory
- External products
- External variants
- Synchronization jobs

The API filters resources using the authenticated user. This helps prevent one user from accessing another user's store-related data.

## Webhook Authentication

Webhook endpoints are intentionally not authenticated using JWT because external providers call them directly.

Instead, webhook requests use:

- Store identification headers
- Provider-specific signature headers
- A secret associated with the store
- HMAC signature verification

Supported webhook signature headers include:

```text
X-Webhook-Signature
X-Shopify-Hmac-Sha256
X-WC-Webhook-Signature
```

Webhook authentication is separate from user authentication.

## Security Recommendations

### Protect Secrets

Never commit the following values:

- Django secret key
- JWT tokens
- Provider API credentials
- Webhook secrets
- Database passwords
- Redis credentials
- Encryption keys

Keep secrets in environment variables or a managed secret store.

### Use HTTPS

Production API traffic should use HTTPS so that access tokens and other sensitive data are encrypted in transit.

### Avoid Logging Tokens

Do not print access tokens, refresh tokens, authorization headers, or provider secrets in application logs.

### Keep Access Tokens Short-Lived

The current access-token lifetime is 30 minutes. Short-lived access tokens reduce the window in which a stolen access token can be used.

### Rotate Refresh Tokens

Refresh-token rotation helps limit the reuse of refresh tokens. Clients should securely replace the old refresh token with the newly issued token.

## Authentication Testing

Run the full Django test suite:

```bash
python manage.py test
```

Run Django system checks:

```bash
python manage.py check
```

### Recommended Manual Tests

#### Test 1: Access a Protected Endpoint Without a Token

```bash
curl -i http://127.0.0.1:8000/api/auth/me/
```

Expected result:

```text
401 Unauthorized
```

#### Test 2: Access a Protected Endpoint With a Valid Token

```bash
curl http://127.0.0.1:8000/api/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected result:

```text
200 OK
```

#### Test 3: Use an Invalid Token

```bash
curl -i http://127.0.0.1:8000/api/auth/me/ \
  -H "Authorization: Bearer invalid-token"
```

Expected result:

```text
401 Unauthorized
```

#### Test 4: Refresh a Valid Refresh Token

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

Expected result:

- A new access token is returned.
- With rotation enabled, a new refresh token is returned.

#### Test 5: Reuse a Rotated Refresh Token

After a refresh token has been rotated and blacklisted, attempt to use the old refresh token again.

Expected result:

```text
The old refresh token is rejected.
```

## Current Authentication Limitations

- JWT authentication is configured for API access.
- Refresh-token rotation and blacklisting are enabled.
- Token storage responsibility remains with the client.
- The project does not currently document a frontend-specific token storage strategy.
- Production deployment should use HTTPS and a secure secret-management solution.
