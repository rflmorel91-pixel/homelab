# Nextcloud → OpenMediaVault Storage Migration

## Overview

The homelab Nextcloud installation was migrated from local Docker volume storage to centralized OpenMediaVault (OMV) NAS storage.

Nextcloud continues to run in Docker on the Ubuntu Server VM, while user file data is stored on an OMV SMB share.

The migration was performed without reinstalling Nextcloud or changing the database.

## Environment

| Component               | Configuration                    |
| ----------------------- | -------------------------------- |
| Hypervisor              | Proxmox VE 9.2.5                 |
| Docker host             | Ubuntu Server                    |
| Nextcloud               | 34.0.2                           |
| Nextcloud container     | `nextcloud`                      |
| Database                | MariaDB 11                       |
| Cache                   | Redis 7 Alpine                   |
| NAS                     | OpenMediaVault                   |
| NAS protocol            | SMB 3.0 / CIFS                   |
| OMV share               | `//192.168.1.137/Data`           |
| Ubuntu mount            | `/mnt/omv-data`                  |
| Nextcloud OMV data path | `/mnt/omv-data/docker/nextcloud` |

## Storage Architecture

```text
                    ┌─────────────────────┐
                    │      Nextcloud      │
                    │    Docker Container │
                    └──────────┬──────────┘
                               │
                               │ /var/www/html/data/nextcloud
                               ▼
                    ┌─────────────────────┐
                    │   Docker Bind Mount │
                    │ /mnt/omv-data/...   │
                    └──────────┬──────────┘
                               │
                               │ SMB 3.0 / CIFS
                               ▼
                    ┌─────────────────────┐
                    │   OpenMediaVault    │
                    │      NAS Storage    │
                    └─────────────────────┘
```

## Original Storage

Originally, the Nextcloud application and data were stored in the Docker volume:

```text
nextcloud_nextcloud_data
```

The Docker volume was located at:

```text
/var/lib/docker/volumes/nextcloud_nextcloud_data/_data
```

The Nextcloud user's primary data directory contained approximately:

```text
48 GB
```

## OMV Storage Preparation

The OMV SMB share was mounted at:

```text
/mnt/omv-data
```

The Docker storage directories were created:

```text
/mnt/omv-data/docker/backups
/mnt/omv-data/docker/nextcloud
/mnt/omv-data/docker/immich
/mnt/omv-data/docker/documents
```

A separate backup location was also created:

```text
/mnt/omv-data/backups
```

## SMB Mount

The OMV share is mounted using CIFS/SMB 3.0.

The relevant `/etc/fstab` configuration uses:

```text
//192.168.1.137/Data /mnt/omv-data cifs credentials=/etc/samba/omv-credentials,vers=3.0,uid=33,gid=33,file_mode=0660,dir_mode=0770,_netdev,nofail,x-systemd.automount 0 0
```

The mount was verified with:

```bash
findmnt /mnt/omv-data
```

The filesystem was confirmed as:

```text
cifs
```

with SMB 3.0 enabled.

## Storage Capacity

The OMV share reported:

```text
Filesystem            Size  Used Avail Use%
//192.168.1.137/Data  196G   48G  149G  25%
```

This confirmed that the migrated Nextcloud data was physically occupying approximately 48 GB on OMV.

## Docker Storage Test

Docker was first tested independently against the OMV mount.

A test file was created:

```bash
mkdir -p /mnt/omv-data/docker-test
echo "Docker OMV storage test" > /mnt/omv-data/docker-test/test.txt
```

Docker successfully read the file:

```bash
docker run --rm \
  -v /mnt/omv-data/docker-test:/data \
  alpine \
  cat /data/test.txt
```

Result:

```text
Docker OMV storage test
```

Docker also successfully created a file on OMV:

```bash
docker run --rm \
  -v /mnt/omv-data/docker-test:/data \
  alpine \
  sh -c 'echo "Created by Docker on OMV" > /data/docker-created.txt'
```

The file was then verified directly from Ubuntu.

The temporary test directory was removed afterward.

## Data Migration

The Nextcloud user data was copied from the existing Docker volume to OMV.

Source:

```text
/var/lib/docker/volumes/nextcloud_nextcloud_data/_data/data/nextcloud/
```

Destination:

```text
/mnt/omv-data/docker/nextcloud/
```

The data size was verified before and after migration:

```text
Source:       48G
OMV:          48G
```

A dry-run comparison using `rsync` produced no pending differences:

```bash
sudo rsync -aHAXn --delete \
  /var/lib/docker/volumes/nextcloud_nextcloud_data/_data/data/nextcloud/ \
  /mnt/omv-data/docker/nextcloud/
```

## Docker Compose Configuration

The Nextcloud application originally used:

```yaml
volumes:
  - nextcloud_data:/var/www/html
```

The OMV bind mount was added underneath the Nextcloud data directory:

```yaml
volumes:
  - nextcloud_data:/var/www/html
  - /mnt/omv-data/docker/nextcloud:/var/www/html/data/nextcloud
```

This allows the existing Nextcloud application files to remain in the Docker volume while the user's data is stored on OMV.

The Docker Compose configuration was validated with:

```bash
sudo docker-compose config
```

Result:

```text
COMPOSE CONFIG OK
```

## Container Verification

The running Nextcloud container was inspected:

```bash
docker inspect nextcloud --format \
'{{range .Mounts}}{{println .Type .Source "->" .Destination}}{{end}}'
```

Result:

```text
bind /mnt/omv-data/docker/nextcloud -> /var/www/html/data/nextcloud
volume /var/lib/docker/volumes/nextcloud_nextcloud_data/_data -> /var/www/html
```

This confirmed that the OMV storage is actively mounted inside the container.

## Nextcloud Health Verification

Nextcloud status was checked using:

```bash
docker exec -u www-data nextcloud php occ status
```

Result:

```text
installed: true
version: 34.0.2.1
versionstring: 34.0.2
maintenance: false
needsDbUpgrade: false
productname: Nextcloud
```

Nextcloud was therefore running normally after the storage change.

## Permissions Verification

The container was tested using the Nextcloud web server user:

```text
UID 33
GID 33
```

Docker successfully created and deleted a test file on the OMV-backed path:

```bash
docker run --rm \
  --user 33:33 \
  -v /mnt/omv-data/docker/nextcloud:/data \
  alpine \
  sh -c 'touch /data/.nextcloud-write-test && echo "WRITE OK" && rm /data/.nextcloud-write-test'
```

Result:

```text
WRITE OK
```

This confirmed that the Nextcloud container has the required write permissions.

## Nextcloud Filesystem Scan

A complete filesystem scan was performed:

```bash
docker exec -u www-data nextcloud php occ files:scan --path="nextcloud/files"
```

Final verification reported:

```text
Errors: 0
```

This confirmed that Nextcloud could successfully read and index the migrated filesystem.

## Real File Verification

An existing Nextcloud file was selected:

```text
Documents/2400297.pdf
```

The file was verified inside the container:

```text
/var/www/html/data/nextcloud/files/Documents/2400297.pdf
```

Size:

```text
33K
```

The same file was verified directly on OMV:

```text
/mnt/omv-data/docker/nextcloud/files/Documents/2400297.pdf
```

Size:

```text
33K
```

The matching file size and path confirmed that the Nextcloud file was physically stored on OMV.

## Web Access Verification

Nextcloud was tested through the web interface.

The application responded successfully on the local Docker port:

```text
http://localhost:8080
```

The application redirected to the configured HTTPS hostname:

```text
https://cloud.fieldlookers.com/login
```

The existing PDF was downloaded through the Nextcloud web interface and successfully opened on the client computer.

This verified the end-to-end read/download path:

```text
Browser
   ↓
Nextcloud HTTPS
   ↓
Nextcloud Docker
   ↓
OMV SMB storage
   ↓
User file
```

## Final Verification Results

| Test                          | Result |
| ----------------------------- | ------ |
| OMV SMB mount                 | PASS   |
| SMB 3.0 connectivity          | PASS   |
| Docker read from OMV          | PASS   |
| Docker write to OMV           | PASS   |
| Nextcloud permissions         | PASS   |
| 48 GB data migration          | PASS   |
| Source/destination comparison | PASS   |
| Docker bind mount             | PASS   |
| Nextcloud status              | PASS   |
| Filesystem scan               | PASS   |
| Filesystem scan errors        | 0      |
| Existing file on OMV          | PASS   |
| Web access                    | PASS   |
| Web download                  | PASS   |

## Rollback Plan

The original Docker volume has intentionally **not** been deleted.

Original volume:

```text
nextcloud_nextcloud_data
```

Original data location:

```text
/var/lib/docker/volumes/nextcloud_nextcloud_data/_data
```

A backup of the Docker container configuration was also created:

```text
~/nextcloud-container-backup.json
```

A backup copy of the Docker Compose file was created:

```text
/opt/stacks/nextcloud/docker-compose.yml.backup
```

If rollback is required:

1. Stop the Nextcloud application.
2. Remove the OMV bind mount from the Compose configuration.
3. Restore the original Compose configuration if necessary.
4. Start the Nextcloud application.
5. Verify the original Docker volume is being used.
6. Run a Nextcloud filesystem scan.
7. Confirm web access and file availability.

The original Docker data should **not be deleted until the OMV-backed configuration has been stable and independently backed up**.

## Lessons Learned

### 1. Verify mount permissions before migration

The SMB mount initially used permissions that prevented UID 33 (`www-data`) from writing.

The mount was corrected to use:

```text
uid=33
gid=33
file_mode=0660
dir_mode=0770
```

### 2. Validate Docker access independently

Testing the OMV mount directly with Docker before modifying Nextcloud helped isolate storage and permission problems.

### 3. Use real files for validation

Creating test objects through the web interface initially resulted in directories with `.txt` names.

Existing real files provided a cleaner way to validate the final storage path.

### 4. Keep a rollback path

The original Docker volume remains available until the new architecture has been proven stable.

## Result

The Nextcloud user data storage migration from local Docker volume storage to OpenMediaVault SMB storage was successfully completed.

Nextcloud continues to run normally while approximately 48 GB of user data is now stored on centralized OMV NAS storage.

The migration was verified at the filesystem, Docker, Nextcloud, and web-application levels.

