# Platform Developer Demonstration

Status: Verified internal demonstration
Platform version: `0.1.1`
Supported contract: Platform Contract v1
Estimated duration: 15 minutes

---

## 1. Goal

This runbook demonstrates that a developer can create and install an
independent SaaS product without modifying platform-core registration,
routing, model-discovery, migration-discovery, or authorization code.

The demonstration verifies:

- Supported command discovery
- Standalone product generation
- Plugin installation
- Contract validation
- Explicit database configuration
- Platform migration execution
- Application startup
- Automatic product discovery
- Product database synchronization
- Product route availability
- Isolated cleanup

This is a developer-experience demonstration, not a production
deployment procedure.

---

## 2. Prerequisites

The developer needs:

- A clone of the `homelab` repository
- Python `3.14` or newer
- Docker
- `curl`
- Git
- Access to install Python dependencies

Public package installation is not supported. The platform is installed
from the checked-out source tree.

Before starting:

    cd ~/homelab

    git status --short

The repository should be clean.

---

## 3. Safety and Isolation

The demonstration uses:

- A temporary working directory
- An isolated Python virtual environment
- A generated standalone plugin
- A disposable PostgreSQL container
- Demo-only database credentials
- A demo-only JWT secret
- A temporary API process
- Localhost-only ports

The cleanup handler stops the API process and database container when
the shell block exits.

No production credentials, databases, services, or customer data are
used.

---

## 4. Demonstration Procedure

Run this complete block from a shell:

    cd ~/homelab/saas/jobflow/backend

    demo_root="$(
      mktemp -d
    )"
    demo_db="saas-platform-demo-db-$$"
    demo_port="55432"
    demo_api_port="8011"
    demo_api_pid=""

    cleanup_demo() {
      if [ -n "$demo_api_pid" ]; then
        kill "$demo_api_pid" 2>/dev/null || true
        wait "$demo_api_pid" 2>/dev/null || true
      fi

      docker stop "$demo_db" >/dev/null 2>&1 || true
    }

    trap cleanup_demo EXIT

    echo "Demo root: $demo_root"
    echo "Demo database: $demo_db"

    python3       -m venv       "$demo_root/venv"

    "$demo_root/venv/bin/python"       -m pip install       --editable       .

    "$demo_root/venv/bin/saas-alembic"       --help

    "$demo_root/venv/bin/saas-create-product"       developer-proof       "Developer Proof"       --description       "Independent platform developer demonstration."       --standalone       --root "$demo_root"

    "$demo_root/venv/bin/python"       -m pip install       --no-deps       "$demo_root/developer-proof-product"

    cd /tmp

    env -u DATABASE_URL -u JWT_SECRET       "$demo_root/venv/bin/saas-validate-product"       developer-proof

    docker run       --detach       --rm       --name "$demo_db"       --publish "127.0.0.1:${demo_port}:5432"       --env POSTGRES_DB=platform_demo       --env POSTGRES_USER=platform_demo       --env POSTGRES_PASSWORD=platform-demo-password       postgres:16

    for attempt in $(seq 1 30); do
      if docker exec         "$demo_db"         pg_isready         -U platform_demo         -d platform_demo         >/dev/null 2>&1
      then
        break
      fi

      sleep 1
    done

    export DATABASE_URL="postgresql+psycopg://platform_demo:platform-demo-password@127.0.0.1:${demo_port}/platform_demo"
    export JWT_SECRET="platform-demo-jwt-secret-at-least-32-bytes"

    "$demo_root/venv/bin/saas-alembic"       upgrade head

    "$demo_root/venv/bin/saas-alembic"       heads

    "$demo_root/venv/bin/uvicorn"       app.main:app       --host 127.0.0.1       --port "$demo_api_port"       >"$demo_root/api.log"       2>&1 &

    demo_api_pid="$!"

    for attempt in $(seq 1 30); do
      if curl         --silent         --fail         "http://127.0.0.1:${demo_api_port}/api/v1/health"         >/dev/null
      then
        break
      fi

      sleep 1
    done

    printf '\n===== PLATFORM HEALTH =====\n'

    curl       --silent       --show-error       "http://127.0.0.1:${demo_api_port}/api/v1/health"

    printf '\n\n===== GENERATED PRODUCT =====\n'

    curl       --silent       --show-error       "http://127.0.0.1:${demo_api_port}/api/v1/products/developer-proof/status"

    printf '\n\n===== SYNCHRONIZED PRODUCT RECORD =====\n'

    docker exec       "$demo_db"       psql       -U platform_demo       -d platform_demo       -c       "SELECT slug, name, status, workspace_key FROM products WHERE slug = 'developer-proof';"

    printf '\n===== API LOG =====\n'

    tail -40       "$demo_root/api.log"

    printf '\n===== REPOSITORY STATUS =====\n'

    cd ~/homelab
    git status --short

---

## 5. Expected Evidence

### Command discovery

`saas-alembic --help` should list:

- `heads`
- `current`
- `history`
- `upgrade`
- `downgrade`
- `revision`
- `check`

### Product generation

The generator should report a standalone project under:

`developer-proof-product`

It should also state that no platform-core registration changes are
required.

### Contract validation

Expected result:

    VALID product=developer-proof version=0.1.0 contract=1 public_routers=1 tenant_routers=0 models=no migration_locations=0
    Validated 1 product.

### Migration state

Expected head:

    385d6260b08a (head)

### Platform health

Expected response:

    {"status":"healthy","service":"jobflow-api"}

### Product route

Expected response:

    {"product":"developer-proof","status":"available"}

### Product synchronization

The `products` table should contain an active record with:

- Slug: `developer-proof`
- Name: `Developer Proof`
- Status: `active`
- Workspace key: `developer-proof`

### Repository state

`git status --short` should produce no output.

---

## 6. Troubleshooting

If the API does not become healthy, inspect:

    tail -80 "$demo_root/api.log"

If port `55432` or `8011` is already occupied, choose an unused local
port before rerunning the demonstration.

If Docker cannot start the database, verify:

    docker version

If installation fails, verify:

    python3 --version

Python `3.14` or newer is required.

---

## 7. Facilitator Flow

Suggested timing:

1. Prerequisites and platform boundary — 2 minutes
2. Install platform and inspect commands — 3 minutes
3. Generate and install the product — 3 minutes
4. Validate and migrate — 3 minutes
5. Start the platform and verify discovery — 3 minutes
6. Capture feedback — 1 minute

The facilitator should avoid correcting the developer unless progress is
blocked. Every intervention must be recorded.

---

## 8. Feedback Record

For each external demonstration, record:

- Date
- Developer profile and relevant experience
- Operating system and Python version
- Docker version
- Total completion time
- Steps completed without assistance
- Steps requiring assistance
- Commands or concepts that were unclear
- Errors encountered
- Understanding of the platform/product boundary
- Confidence creating another product
- Requested platform capabilities
- Willingness to use the platform again
- Positive feedback
- Negative feedback
- Exact developer quotes when permission is given

Do not classify an internal author-run demonstration as external
developer validation.

---

## 9. Success Threshold

The demonstration succeeds when an external developer can:

- Complete the journey without author intervention
- Explain why the product does not require platform-core changes
- Identify where the product definition and routes live
- Validate the generated product
- Configure the database explicitly
- Start the application
- Confirm automatic product discovery
- Locate useful failure information
- State whether they would build another product

Any author intervention, undocumented prerequisite, confusing command,
or failed expectation is valid negative evidence and must be preserved.

---

## 10. Current Limitations

- The platform must be installed from source
- Python `3.14` or newer is required
- Docker is required for this demonstration
- Only Platform Contract v1 is supported
- No public package is available
- No durable release artifact is available
- Package naming remains JobFlow-derived
- Bundled reference products remain in the platform wheel
- Production deployment and rollback are outside this runbook

---

## 11. Premature Work Guardrail

Do not add speculative platform capabilities merely to make the
demonstration appear more complete.

A new capability is justified only when the demonstration produces
specific evidence that a developer cannot complete a necessary step
without it.

---

## 12. Roadmap Position

Current position:

Build → Document → **Demonstrate** → Customer Validation → Package →
Sell

This runbook completes the internal preparation for the Demonstrate
stage. It does not establish external developer validation.

---

## 13. Single Next Milestone

Have one external developer complete this runbook without author
intervention and record the resulting positive and negative feedback.

Public packaging, release automation, and additional speculative
platform features remain premature until that evidence exists.
