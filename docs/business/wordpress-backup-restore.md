# WordPress Backup and Restore Runbook

## Purpose

This runbook documents the backup and recovery procedure for the Docker-based WordPress hosting environment used in the homelab.

The objective is to maintain recoverable WordPress application data and demonstrate that backups can be restored and verified.

## Environment

* WordPress: Docker `wordpress:latest`
* Database: MariaDB 11
* Reverse Proxy: Nginx Proxy Manager
* WordPress container: `wordpress`
* Database container: `wordpress-db`
* WordPress URL: `http://wordpress.local`
* WordPress files volume: `wordpress_wordpress_data`
* Database volume: `wordpress_db_data`

## Backup Components

A complete WordPress backup requires both:

1. WordPress application files
2. MariaDB database contents

The backup directory is:

```text
~/homelab-backups/wordpress/
```

Backup artifacts:

```text
wordpress-files.tar.gz
wordpress-db.sql
```

## Database Backup

The MariaDB database is backed up using `mariadb-dump`.

Example:

```bash
docker exec wordpress-db \
  mariadb-dump \
  -u root \
  -p"$(grep '^MYSQL_ROOT_PASSWORD=' .env | cut -d= -f2-)" \
  wordpress > ~/homelab-backups/wordpress/wordpress-db.sql
```

The resulting SQL dump contains the WordPress database schema and application data.

## WordPress File Backup

The WordPress files are archived from inside the running WordPress container:

```bash
docker exec wordpress \
  tar -czf - -C /var/www/html . \
  > ~/homelab-backups/wordpress/wordpress-files.tar.gz
```

This produces a portable compressed archive of the WordPress installation.

## Backup Verification

The verified backup set contained:

```text
wordpress-db.sql          102 KB
wordpress-files.tar.gz     29 MB
```

The file archive was inspected and confirmed to contain WordPress application files, including:

```text
wp-content/
wp-config-docker.php
```

The database dump was inspected and contained 12 WordPress tables.

## Database Restore Test

A temporary MariaDB container was created for recovery testing.

The SQL backup was imported into a separate database:

```bash
docker exec -i wordpress-restore-test-db \
  mariadb \
  -uroot \
  -prestore_test_password \
  wordpress_restore \
  < ~/homelab-backups/wordpress/wordpress-db.sql
```

The restored database contained the expected WordPress tables:

```text
wp_commentmeta
wp_comments
wp_links
wp_options
wp_postmeta
wp_posts
wp_term_relationships
wp_term_taxonomy
wp_termmeta
wp_terms
wp_usermeta
wp_users
```

Total tables restored:

```text
12
```

## Application Data Verification

The restored database was queried to verify actual application data.

Verified site name:

```text
Rafael IT Infrastructure
```

Verified site URL:

```text
http://wordpress.local
```

Verified restored posts:

```text
4
```

This confirmed that the restore contained real WordPress application data rather than only an empty database schema.

## Live Site Verification

After the restore test, the temporary recovery database was removed without modifying the production WordPress containers.

The live WordPress site was tested through Nginx Proxy Manager:

```bash
curl -I -H "Host: wordpress.local" http://localhost
```

Final result:

```text
HTTP/1.1 200 OK
```

## Recovery Validation

The recovery test demonstrated:

```text
WordPress files
      ↓
Compressed backup
      ↓
Database backup
      ↓
Temporary database restore
      ↓
12 tables restored
      ↓
Application data verified
      ↓
Live site verified
```

## Important Lessons

A WordPress backup must include both the application files and database.

The first file-backup attempt produced an invalid 20-byte archive. The live WordPress volume was then inspected and confirmed to contain approximately 94 MB of data.

The file backup was recreated from inside the WordPress container, producing a valid 29 MB archive.

This troubleshooting step demonstrated the importance of verifying backup contents rather than assuming that a backup command succeeded.

## Operational Checklist

* [x] WordPress deployment verified
* [x] MariaDB deployment verified
* [x] WordPress files identified
* [x] Database backup created
* [x] WordPress file backup created
* [x] Backup archive contents verified
* [x] Database dump verified
* [x] Temporary database restore performed
* [x] 12 database tables restored
* [x] Site information verified
* [x] Four WordPress posts verified
* [x] Live WordPress site verified
* [x] Temporary restore environment removed

## Future Improvements

Potential production improvements include:

* Automated scheduled backups
* Backup retention policies
* Off-host backup storage
* Encrypted backup storage
* Backup monitoring and alerting
* Automated restore testing
* Disaster recovery documentation
* Client-specific backup retention policies
* HTTPS for production domains
* External monitoring of hosted websites

## Business Relevance

This procedure forms part of a potential managed WordPress hosting service.

A client-facing service can include:

* WordPress deployment
* Domain and DNS configuration
* HTTPS configuration
* Website maintenance
* Backup and recovery
* Monitoring
* Security hardening
* Documentation
* Disaster recovery testing

The operational model is:

**Deploy → Secure → Monitor → Backup → Verify → Recover → Document**
