# SyncBridge

SyncBridge is a Django-based backend for synchronizing products, inventory, and orders between an internal system and external commerce providers.

The project provides a provider-independent synchronization layer, webhook ingestion, JWT authentication, store-level data isolation, background processing with Celery, and a mock provider for local development and testing.

## Features

- JWT-based authentication using Django REST Framework SimpleJWT
- User-owned stores and integrations
- Provider abstraction for multiple commerce platforms
- Supported providers:
  - Mock Store
  - Shopify
  - WooCommerce
- Product synchronization
- Inventory synchronization
- Order synchronization
- Webhook ingestion and duplicate-event protection
- Background processing with Celery and Redis
- PostgreSQL database support
- Docker and Docker Compose setup
- Automatic database migrations during container startup
- Gunicorn application server
- GitHub Actions CI pipeline
- Store-level permission and ownership filtering
- Mock failure scenarios for testing provider error handling

## Architecture

```text
                         ┌─────────────────────┐
                         │      API Client     │
                         │  Web / Postman / UI │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Django REST API   │
                         │ Authentication      │
                         │ Store Management    │
                         │ Sync Jobs           │
                         │ Webhooks            │
                         └───────┬───────┬─────┘
                                 │       │
                    ┌────────────┘       └─────────────┐
                    ▼                                  ▼
          ┌──────────────────┐                ┌──────────────────┐
          │ Provider Layer   │                │ Webhook Layer    │
          │ Mock             │                │ Validate         │
          │ Shopify          │                │ Verify signature │
          │ WooCommerce      │                │ Deduplicate      │
          └────────┬─────────┘                │ Queue task       │
                   │                          └────────┬─────────┘
                   ▼                                   │
          ┌──────────────────┐                          │
          │ HTTP / Adapters  │                          │
          │ Normalize data   │                          │
          └────────┬─────────┘                          │
                   │                                    │
                   └────────────────┬───────────────────┘
                                    ▼
                         ┌─────────────────────┐
                         │ Celery + Redis      │
                         │ Background Tasks    │
                         │ Retry Handling      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Synchronization     │
                         │ Products            │
                         │ Inventory           │
                         │ Orders              │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ PostgreSQL          │
                         │ Users               │
                         │ Stores              │
                         │ Products            │
                         │ Orders              │
                         │ Sync Jobs           │
                         │ Webhook Events      │
                         └─────────────────────┘
```

## Technology Stack

- **Backend:** Python, Django
- **API:** Django REST Framework
- **Authentication:** SimpleJWT
- **Database:** PostgreSQL
- **Task Queue:** Celery
- **Message Broker / Result Backend:** Redis
- **Application Server:** Gunicorn
- **Containerization:** Docker, Docker Compose
- **CI:** GitHub Actions
- **External Integrations:** Shopify and WooCommerce provider adapters

## Project Structure

```text
.
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── .dockerignore
├── .env.example
├── README.md
├── docs/
│   └── SyncBridge_Project_Checklist.md
└── backend/
    ├── manage.py
    ├── requirements.txt
    ├── config/
    │   ├── settings.py
    │   ├── urls.py
    │   ├── asgi.py
    │   └── wsgi.py
    ├── accounts/
    ├── audit_logs/
    ├── integrations/
    │   ├── http_client.py
    │   └── providers/
    │       ├── base.py
    │       ├── errors.py
    │       ├── factory.py
    │       ├── mock.py
    │       ├── schemas.py
    │       ├── shopify.py
    │       └── woocommerce.py
    ├── mock_store/
    ├── orders/
    ├── products/
    ├── stores/
    ├── synchronization/
    └── webhooks/
```

## Supported Providers

| Provider | Purpose | Status |
|---|---|---|
| Mock Store | Local development, testing, and failure simulation | Supported |
| Shopify | Product, inventory, and order integration | Implemented |
| WooCommerce | Product, inventory, and order integration | Implemented |

Provider-specific responses are converted into normalized internal schemas so that synchronization logic does not need to depend on the original provider response format.

## Core Concepts

### Store

A store belongs to a user and represents an external commerce integration.

Store records include:

- Store name
- Provider/integration
- External store ID
- Store status
- Provider credentials
- Created and updated timestamps

API responses do not expose store credentials.

### Provider Abstraction

The provider layer separates external platform behavior from the synchronization system.

Provider implementations are responsible for:

- Fetching products
- Fetching inventory
- Fetching orders
- Updating inventory where supported
- Translating provider-specific errors
- Normalizing provider responses

The provider factory selects the implementation based on the store's integration provider.

### Normalized Data

Provider adapters normalize external data into common structures, including:

- Products
- Variants
- Inventory
- Orders
- Order items

This allows the synchronization layer to work consistently across providers.

## API Endpoints

The API is served under `/api/`.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/token/` | Obtain access and refresh tokens |
| POST | `/api/auth/token/refresh/` | Refresh an access token |
| GET | `/api/auth/me/` | Return the authenticated user's basic information |

Example token request:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your-password"
  }'
```

Example authenticated request:

```bash
curl http://127.0.0.1:8000/api/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Stores

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/stores/` | List the authenticated user's stores |
| POST | `/api/stores/` | Create a store |
| GET | `/api/stores/<id>/` | Retrieve a store |
| PATCH | `/api/stores/<id>/` | Update a store |
| DELETE | `/api/stores/<id>/` | Delete a store |

Store data is filtered by the authenticated user. Users cannot access or modify another user's stores.

### Products

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/products/` | List products |
| POST | `/api/products/` | Create a product |
| GET | `/api/products/<id>/` | Retrieve a product |
| PATCH | `/api/products/<id>/` | Update a product |
| DELETE | `/api/products/<id>/` | Delete a product |

### Variants

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/variants/` | List product variants |
| POST | `/api/variants/` | Create a variant |
| GET | `/api/variants/<id>/` | Retrieve a variant |
| PATCH | `/api/variants/<id>/` | Update a variant |
| DELETE | `/api/variants/<id>/` | Delete a variant |

### Inventory

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/inventory/` | List inventory records |
| POST | `/api/inventory/` | Create an inventory record |
| GET | `/api/inventory/<id>/` | Retrieve an inventory record |
| PATCH | `/api/inventory/<id>/` | Update an inventory record |
| DELETE | `/api/inventory/<id>/` | Delete an inventory record |

### External Mappings

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/external-products/` | List external product mappings |
| POST | `/api/external-products/` | Create an external product mapping |
| GET | `/api/external-variants/` | List external variant mappings |
| POST | `/api/external-variants/` | Create an external variant mapping |

External mapping endpoints enforce ownership validation through the related product and store.

### Synchronization Jobs

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/sync/jobs/` | List the authenticated user's sync jobs |
| GET | `/api/sync/jobs/<id>/` | Retrieve a sync job and its errors |

Sync jobs are read-only through the API. They include progress information and nested synchronization errors.

### Shopify OAuth

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/integrations/shopify/connect` | Start the Shopify OAuth flow |
| GET | `/api/integrations/shopify/callback/` | Handle the Shopify OAuth callback |

The OAuth flow validates the `state` value stored in the session to help prevent CSRF-style OAuth attacks.

## Synchronization Behavior

Supported synchronization types include:

- `products`
- `inventory`
- `orders`
- `full`

The synchronization runner currently implements:

- Product synchronization
- Inventory synchronization
- Order synchronization

The `full` synchronization type is defined in the model layer but is not currently implemented by the synchronization runner.

### Product Synchronization

Product synchronization:

1. Fetches products from the selected provider.
2. Matches records using the store and external product ID.
3. Creates or updates internal products.
4. Creates or updates product variants.
5. Uses database transactions for related product updates.

### Inventory Synchronization

Inventory synchronization:

1. Fetches inventory data from the provider.
2. Resolves the external variant mapping.
3. Creates or updates internal inventory records.
4. Raises an error when the required external variant mapping is missing.

### Order Synchronization

Order synchronization:

1. Fetches orders from the provider.
2. Maps provider order statuses to internal statuses.
3. Creates or updates orders using the external order ID.
4. Creates or updates order items.
5. Requires external variant mappings for order items.

## Webhooks

Webhook endpoints do not require JWT authentication. They authenticate incoming requests using provider-specific signatures and store credentials.

### Mock Webhook

```text
POST /api/webhooks/mock/
```

Required headers:

- `X-Store-ID`
- `X-Webhook-Signature`

The payload must contain:

- `event_id`
- `event_type`

### Shopify Webhook

```text
POST /api/webhooks/shopify/
```

Required headers:

- `X-Store-ID`
- `X-Shopify-Hmac-Sha256`
- `X-Shopify-Webhook-Id`
- `X-Shopify-Topic`

Shopify signatures use Base64-encoded HMAC-SHA256 verification.

### WooCommerce Webhook

```text
POST /api/webhooks/woocommerce/
```

Required headers:

- `X-Store-ID`
- `X-WC-Webhook-Signature`
- `X-WC-Webhook-ID`
- `X-WC-Webhook-Topic`

WooCommerce signatures use HMAC-SHA256 verification.

### Webhook Processing Flow

1. Validate required headers.
2. Resolve the store.
3. Confirm the store uses the expected provider.
4. Verify the webhook signature.
5. Parse and validate the JSON body.
6. Check for duplicate webhook events.
7. Save the webhook event.
8. Dispatch background processing after the database transaction commits.
9. Update the webhook status during processing.

Webhook events have statuses such as:

- `received`
- `processing`
- `processed`
- `failed`

A unique constraint on the store and event ID helps prevent duplicate event records.

The current webhook business-processing function is a placeholder. The event lifecycle and background task structure are implemented, but provider-specific business actions still need to be expanded.

## Error and Retry Behavior

Provider errors are represented by custom exceptions, including:

- `ProviderError`
- `AuthenticationError`
- `NotFoundError`
- `RateLimitError`
- `TemporaryProviderError`
- `ProviderRequestError`

Retryable errors include rate-limit and temporary provider errors.

The synchronization and webhook Celery tasks are configured with:

- Maximum retries: `3`
- Retry countdown: `2` seconds

The HTTP client uses the following default timeouts:

- Connection timeout: `3` seconds
- Read timeout: `10` seconds

Provider responses such as HTTP 400, 401, 404, 429, and 500 are translated into appropriate provider exceptions.

## Mock Provider

The mock provider is available for local development and automated testing.

### Mock Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/mock-store/products/` | Return mock products |
| GET | `/api/mock-store/inventory/` | Return mock inventory |
| GET | `/api/mock-store/orders/` | Return mock orders |
| PATCH | `/api/mock-store/inventory/<external_variant_id>/` | Update mock inventory |

### Failure Simulation

The mock API supports failure simulation using query parameters.

Examples:

```text
?failure=400
?failure=401
?failure=404
?failure=429
?failure=500
```

Additional simulation options include:

```text
?simulate=401
?simulate=404
?simulate=429
?simulate=500
?simulate=slow
?simulate=duplicate
```

The slow simulation delays the response, while the duplicate simulation returns a duplicate product to test deduplication and synchronization behavior.

## Local Development

### Prerequisites

Install the following tools:

- Python 3.13
- PostgreSQL 17
- Redis
- Git
- Docker Desktop (recommended)

### Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
cd syncBridge
```

### Create and Activate a Virtual Environment

From the project root:

```bash
cd backend
python -m venv venv
```

Git Bash:

```bash
source venv/Scripts/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Copy the example environment file:

```bash
cp ../.env.example ../.env
```

Update the values in `.env`.

At minimum, configure:

```dotenv
POSTGRES_DB=syncbridge
POSTGRES_USER=syncbridge
POSTGRES_PASSWORD=change_me
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

DJANGO_SECRET_KEY=replace_with_a_secure_secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

REDIS_URL=redis://localhost:6379/0
```

Do not commit `.env` or real credentials to version control.

### Run Migrations

```bash
python manage.py migrate
```

### Create a Superuser

```bash
python manage.py createsuperuser
```

### Run Django

```bash
python manage.py runserver
```

The development server will be available at:

```text
http://127.0.0.1:8000/
```

### Run Celery

From the `backend` directory with the virtual environment activated:

```bash
celery -A config worker --loglevel=INFO --pool=solo
```

Redis must be running before starting the Celery worker.

### Run Tests

```bash
python manage.py test
```

### Run Django Checks

```bash
python manage.py check
```

## Docker Development

From the project root:

```bash
docker compose up --build
```

The Compose setup starts:

- PostgreSQL
- Redis
- Django/Gunicorn backend

The backend container:

1. Checks the database connection.
2. Runs database migrations.
3. Starts Gunicorn.

To stop the services:

```bash
docker compose down
```

To stop services and remove persisted volumes:

```bash
docker compose down -v
```

The second command deletes local PostgreSQL and Redis data. Use it only when data removal is intended.

## CI

GitHub Actions runs on pushes and pull requests targeting the `master` branch.

The CI workflow:

1. Checks out the repository.
2. Sets up Python 3.13.
3. Installs dependencies.
4. Runs Django system checks.
5. Runs the Django test suite against PostgreSQL.

The workflow is located at:

```text
.github/workflows/ci.yml
```

## Deployment

The application has been deployed and tested on Render as an API service.

The deployed API should be configured with environment variables for:

- Django secret key
- Debug mode
- Allowed hosts
- Database connection
- Redis connection
- Provider credentials
- Encryption-related secrets where applicable

For a production deployment:

- Set `DJANGO_DEBUG=False`.
- Use a strong, unique Django secret key.
- Restrict `DJANGO_ALLOWED_HOSTS`.
- Use managed PostgreSQL and Redis services.
- Do not use development credentials.
- Configure HTTPS.
- Configure provider secrets through the hosting platform's secret manager.
- Run Celery workers separately from the web service.
- Plan database migrations as a controlled deployment step.
- Configure production email delivery if email functionality is introduced.
- Review static file serving and collection requirements.

The current Docker entrypoint runs migrations when the backend container starts. This is suitable for the current single-container setup, but a separate migration job is preferable for multi-instance production deployments.

## Security Notes

- JWT authentication protects authenticated API endpoints.
- Store, product, variant, inventory, and synchronization queries are filtered by the authenticated user.
- Store credentials are excluded from store API serializers.
- Webhook signatures are verified before accepting events.
- Webhook event IDs are used for duplicate detection.
- Django CSRF middleware remains enabled.
- Secrets are loaded from environment variables.
- CORS is not broadly enabled. Configure restricted frontend origins when a frontend is introduced.
- Never commit `.env`, access tokens, provider secrets, or production credentials.

## Current Limitations

- Store credentials are stored in a JSON field and are not yet encrypted at the database-field level.
- Full synchronization is defined but not implemented in the synchronization runner.
- Webhook business processing is currently a placeholder.
- Shopify OAuth callback validation is implemented, but complete token persistence and provider onboarding require further work.
- Production Celery worker deployment is not included in the current single-service deployment.
- Production email delivery is not configured.
- Linting and formatting checks are intentionally not included in the current CI workflow.

## Useful Commands

```bash
# Run Django checks
python manage.py check

# Apply migrations
python manage.py migrate

# Create migrations
python manage.py makemigrations

# Run tests
python manage.py test

# Start development server
python manage.py runserver

# Start Celery worker
celery -A config worker --loglevel=INFO --pool=solo

# Start Docker services
docker compose up --build

# View backend container logs
docker compose logs -f backend

# View all container logs
docker compose logs -f
```

## Project Status

SyncBridge currently includes:

- Django REST API
- JWT authentication
- Store ownership and permission controls
- Mock, Shopify, and WooCommerce provider integrations
- Product, inventory, and order synchronization foundations
- Webhook ingestion and duplicate protection
- Celery task infrastructure
- Docker Compose support
- Gunicorn startup
- PostgreSQL and Redis health checks
- GitHub Actions test automation
- Render deployment testing

The project is actively extensible and can be expanded with additional providers, complete webhook business processing, full synchronization orchestration, encrypted credential storage, and a more complete production deployment architecture.
