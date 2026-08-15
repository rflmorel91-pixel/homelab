# WordPress Hosting Service

## Service Overview

A small-business WordPress hosting and website infrastructure service focused on reliable deployment, secure configuration, backups, monitoring, and basic website infrastructure.

The service is designed for small businesses, professionals, freelancers, and organizations that need a simple WordPress website without managing the underlying server infrastructure themselves.

## Starter Hosting Package

**Target price: $250–$350 initial setup**

### Included

* WordPress installation and configuration
* MariaDB database deployment
* Docker-based application deployment
* Reverse proxy configuration
* Domain and DNS configuration assistance
* HTTPS configuration
* Basic WordPress security configuration
* Persistent WordPress storage
* Database backup
* WordPress file backup
* Backup verification
* Basic uptime monitoring
* Deployment documentation
* Handoff documentation

## Backup and Recovery

The hosting environment uses separate backups for:

1. WordPress application files
2. WordPress MariaDB database

Backups are verified rather than assumed to be valid.

The documented recovery process includes:

* Database restore testing
* Verification of restored WordPress tables
* Verification of application data
* Live-site validation

## Optional Services

### Website Maintenance

**$50–$100/month**

Potential services:

* WordPress updates
* Plugin updates
* Theme updates
* Basic health checks
* Backup verification
* Uptime monitoring

### Backup and Disaster Recovery

**$100–$200 setup**

Potential services:

* Automated backups
* Backup retention
* Off-host backup storage
* Recovery testing
* Disaster recovery documentation

### Website Infrastructure Setup

**$200–$350**

Potential services:

* Domain configuration
* DNS configuration
* Reverse proxy
* HTTPS
* WordPress deployment
* Database deployment
* Monitoring

## Client Responsibilities

The client provides:

* Domain ownership or authorized DNS access
* Website content
* Logo and branding assets
* Required WordPress account information
* Required third-party service credentials
* Authorization for infrastructure changes

The client remains responsible for ownership and licensing of their website content, themes, plugins, images, and other third-party assets.

## Scope Boundaries

The starter package does not automatically include:

* Custom web application development
* Complex custom WordPress plugins
* Custom theme development
* E-commerce development
* SEO campaigns
* Paid advertising
* Content creation
* Graphic design
* Advanced database optimization
* Unlimited support
* Third-party licensing fees

Additional work should be quoted separately.

## Security Practices

The hosting workflow follows basic infrastructure security practices:

* Credentials stored outside Git
* `.env` excluded from version control
* Persistent application storage
* Database separation
* Reverse proxy
* HTTPS for production deployments
* Backup verification
* Limited technical access
* Documented infrastructure

Production client environments should receive a security review before being exposed to the public Internet.

## Monitoring

A hosted WordPress installation can be monitored for:

* Website availability
* HTTP response status
* Server health
* Disk usage
* Memory usage
* Container availability

The homelab monitoring platform uses Prometheus, Grafana, Node Exporter, cAdvisor, and Uptime Kuma as the infrastructure monitoring foundation.

## Onboarding Process

The proposed client workflow is:

1. Initial discovery call
2. Identify website and infrastructure requirements
3. Assess domain and DNS configuration
4. Define project scope
5. Provide price and deliverables
6. Obtain client approval
7. Deploy infrastructure
8. Configure WordPress
9. Configure domain and HTTPS
10. Configure backups
11. Test website
12. Verify recovery capability
13. Provide client handoff
14. Begin optional maintenance

## Delivery Checklist

* [ ] Client requirements documented
* [ ] Domain ownership verified
* [ ] Project scope approved
* [ ] Hosting environment deployed
* [ ] WordPress configured
* [ ] Database configured
* [ ] Domain configured
* [ ] HTTPS configured
* [ ] Backup configured
* [ ] Backup verified
* [ ] Monitoring configured
* [ ] Website tested
* [ ] Recovery procedure verified
* [ ] Client handoff completed

## Business Positioning

The service is positioned around infrastructure reliability rather than simply installing WordPress.

The value proposition is:

**Deploy → Secure → Monitor → Backup → Verify → Support**

The goal is to provide small businesses with a professionally managed foundation for their website while keeping the initial project small, clearly defined, and affordable.

## Relationship to First $1,000 Goal

The first revenue milestone can be reached through several small infrastructure projects rather than one large engagement.

Example:

* WordPress hosting setup — $300
* Backup and recovery setup — $250
* Monitoring setup — $200
* Linux security hardening — $200

**Potential total: $950**

Additional maintenance or a small website project could bring the first milestone above $1,000.
