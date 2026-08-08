## Deployment Verification

The external access architecture was tested from the Ubuntu Server after deployment.

### Cloudflare Tunnel

The Cloudflare Tunnel service was confirmed active:

```text
cloudflared: active
```

The tunnel reported an active Linux connector running `cloudflared 2026.7.3`.

### Docker Services

The following services were confirmed running:

```text
nextcloud
nextcloud-db
nextcloud-redis
vaultwarden
authentik
authentik-worker
authentik-postgres
authentik-redis
nginx-proxy-manager
```

Nextcloud, Vaultwarden, and Authentik were operational, with the relevant health checks passing.

### Public HTTPS Verification

The three public hostnames were tested using `curl`.

#### Nextcloud

```text
https://cloud.fieldlookers.com
```

Result:

```text
HTTP/2 302
Location: https://cloud.fieldlookers.com/login
Server: cloudflare
```

The redirect to the Nextcloud login page confirms that the public request successfully reached the Nextcloud application.

#### Vaultwarden

```text
https://vault.fieldlookers.com
```

Result:

```text
HTTP/2 200
Server: cloudflare
```

Vaultwarden successfully responded through the public HTTPS endpoint.

#### Authentik

```text
https://auth.fieldlookers.com
```

Result:

```text
HTTP/2 302
Location: /flows/-/default/authentication/?next=/
Server: cloudflare
X-Powered-By: authentik
```

The redirect confirms that the public request successfully reached Authentik's authentication flow.

### Verification Summary

| Component                 | Result                   |
| ------------------------- | ------------------------ |
| Cloudflare Tunnel         | Verified                 |
| Tunnel connector          | Verified                 |
| Nginx Proxy Manager       | Verified                 |
| HTTPS / port 443          | Verified                 |
| Nextcloud public access   | Verified                 |
| Vaultwarden public access | Verified                 |
| Authentik public access   | Verified                 |
| Cloudflare DNS routing    | Verified                 |
| 502 errors                | None during verification |
| 522 errors                | None during verification |

### Final Verified Path

```text
Internet
    │
    ▼
Cloudflare
    │
    ▼
Cloudflare Tunnel
    │
    ▼
Ubuntu Server
    │
    ▼
Nginx Proxy Manager
    │
    ├── cloud.fieldlookers.com
    │       └── Nextcloud
    │
    ├── vault.fieldlookers.com
    │       └── Vaultwarden
    │
    └── auth.fieldlookers.com
            └── Authentik
```

**Deployment status: VERIFIED**

The homelab's three public services were successfully tested through their external HTTPS endpoints and returned the expected application responses.
