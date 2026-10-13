PrestamoDesk private review documents — isolated staging overlay

Apply only to /home/rflmorel/homelab-prestamodesk-review-staging on branch
infrastructure/isolated-staging. This archive excludes production compose and
the public inquiry page.

On DellPC:
  cd /home/rflmorel/homelab-prestamodesk-review-staging
  git status --short --branch
  unzip -o /tmp/prestamodesk-private-documents-staging.zip -d .
  git diff --check
  cd saas/jobflow/staging
  docker-compose --project-name fieldlookers-review \
    --project-directory "$PWD" \
    --env-file "$PWD/.runtime/runtime.env" \
    -f "$PWD/compose.yml" up -d --build

Storage: 8 MiB limit; PDF/JPEG/PNG magic checks; generated UUIDs;
manager-authenticated tenant/application-scoped upload and attachment download;
private named staging volume with 0700 directories and 0600 files. Approval
requires matching uploaded identity/income/vehicle-registration metadata;
conversion requires the uploaded signed-contract record. This filesystem store
is for isolated synthetic-data staging; it is not an encrypted production store.
