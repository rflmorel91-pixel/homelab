# AssetTrack Developer API v1

Status: private preview

## Purpose

AssetTrack gives small IT firms, MSPs, and software developers a
tenant-isolated API for customer equipment and append-only service
history.

## Base URL

    https://jobflow.fieldlookers.com/api/v1/products/assettrack/developer/v1

## Authentication

Send an AssetTrack API key as a Bearer credential:

    Authorization: Bearer flk_at_<secret>

Each key belongs to one AssetTrack tenant. Developer requests do not
use the `X-Tenant-ID` header.

Only a tenant owner can create, list, or revoke API keys. The complete
key is returned once when it is created. FieldLookers stores only its
SHA-256 hash.

Keep keys in server-side secret storage. Never commit them to source
control, expose them in browser code, or include them in logs.

## Verify a key

    curl --fail-with-body \
      --header "Authorization: Bearer $ASSETTRACK_API_KEY" \
      https://jobflow.fieldlookers.com/api/v1/products/assettrack/developer/v1/status

Successful response:

    {
      "product": "assettrack",
      "api_version": "v1",
      "status": "available"
    }

## Assets

### Fields

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `external_id` | string or null | no | Unique inside the tenant |
| `name` | string | yes | Display name |
| `asset_type` | string | no | Defaults to `other` |
| `manufacturer` | string or null | no | Manufacturer name |
| `model` | string or null | no | Model name or number |
| `serial_number` | string or null | no | Manufacturer serial |
| `status` | string | no | Defaults to `active` |
| `attributes` | object | no | Integration-specific data |

Allowed status values are `active`, `inactive`, `retired`, and
`lost`.

Responses also contain `id`, `created_at`, and `updated_at`.

### Create an asset

    curl --fail-with-body \
      --request POST \
      --header "Authorization: Bearer $ASSETTRACK_API_KEY" \
      --header "Content-Type: application/json" \
      --data '{
        "external_id": "msp-device-100",
        "name": "Customer firewall",
        "asset_type": "network_device",
        "manufacturer": "Netgate",
        "model": "6100",
        "serial_number": "FW-6100-100",
        "attributes": {
          "site": "Main office"
        }
      }' \
      https://jobflow.fieldlookers.com/api/v1/products/assettrack/developer/v1/assets

A successful request returns HTTP `201`. Reusing an `external_id`
inside the same tenant returns HTTP `409`.

### List assets

    GET /assets?limit=100&offset=0&asset_type=network_device&status=active

`limit` must be between 1 and 500. `offset` must be zero or greater.
The `asset_type` and `status` filters are optional.

### Retrieve, replace, or delete

    GET    /assets/{asset_id}
    PUT    /assets/{asset_id}
    DELETE /assets/{asset_id}

`PUT` requires the complete writable asset representation. A
successful deletion returns HTTP `204` and also removes that asset's
service-event history.

## Service history

Service history is append-only through the v1 developer contract.

### Event fields

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `event_type` | string | yes | Event category |
| `occurred_at` | datetime | yes | ISO 8601 timestamp |
| `summary` | string | yes | Short description |
| `details` | object | no | Ticket IDs or other data |

### Append an event

    POST /assets/{asset_id}/service-events

Example body:

    {
      "event_type": "maintenance",
      "occurred_at": "2026-09-05T18:00:00Z",
      "summary": "Updated firewall firmware",
      "details": {
        "ticket": "MSP-2001"
      }
    }

### List events

    GET /assets/{asset_id}/service-events?limit=100&offset=0

Events are ordered by occurrence time and ID.

## Errors

| Status | Meaning |
| --- | --- |
| `401` | API key is missing, malformed, invalid, or revoked |
| `403` | Product or tenant is suspended or unavailable |
| `404` | Asset does not exist in the key's tenant |
| `409` | External asset ID conflicts inside the tenant |
| `422` | Request validation failed |

All resource queries are tenant-scoped.

## Key administration

Key administration uses an authenticated AssetTrack owner session and
the `X-Tenant-ID` header:

    POST   /api/v1/products/assettrack/developer-api-keys
    GET    /api/v1/products/assettrack/developer-api-keys
    DELETE /api/v1/products/assettrack/developer-api-keys/{key_id}

Create request:

    {
      "name": "Production MSP integration"
    }

The creation response contains `api_key` exactly once. Key listings
never return the secret or its hash.

## Preview boundaries

This private preview does not yet promise a public SLA, usage quota,
webhooks, client SDKs, or self-service billing. Those features require
commercial validation before expansion.
