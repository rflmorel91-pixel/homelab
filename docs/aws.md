# AWS Cloud Infrastructure

## Overview

AWS cloud infrastructure was added as part of the 90-day IT program to extend the homelab skills into a public cloud environment.

The AWS environment demonstrates:

- AWS IAM Identity Center
- MFA
- AWS CLI authentication using SSO
- VPC inspection
- Subnet and routing inspection
- EC2 provisioning
- Security Groups
- Ubuntu Server administration
- UFW firewall configuration
- SSH key-based access
- Remote server verification

## AWS Account Configuration

| Component | Configuration |
|---|---|
| AWS Region | us-east-2 |
| Authentication | IAM Identity Center |
| CLI Profile | rafael-aws |
| Permission Set | AdministratorAccess |
| MFA | Enabled |
| CLI Version | AWS CLI 2.31.35 |

AWS CLI authentication was verified using:

```bash
aws sts get-caller-identity --profile rafael-aws

172.31.0.0/16 → local
0.0.0.0/0     → Internet Gateway

igw-0fc7f51069272f703

homelab-aws-sg
sg-0b408188f3577bdfc

TCP/22
69.127.140.117/32

Status: active
Logging: on (low)
Default: deny (incoming)
Default: allow (outgoing)
Default: disabled (routed)

22/tcp
ALLOW IN
69.127.140.117

Internet
   |
   v
AWS Security Group
   |
   v
Ubuntu UFW
   |
   v
SSH
   |
   v
Ubuntu Server

Hostname: ip-172-31-1-63
Ubuntu: Ubuntu 24.04.4 LTS
Release: 24.04
Codename: noble
Architecture: x86_64
Kernel: 6.17.0-1019-aws

aws sts get-caller-identity --profile rafael-aws

aws ec2 describe-vpcs \
  --profile rafael-aws \
  --region us-east-2

aws ec2 describe-subnets \
  --profile rafael-aws \
  --region us-east-2

aws ec2 describe-route-tables \
  --profile rafael-aws \
  --region us-east-2

aws ec2 describe-instances \
  --profile rafael-aws \
  --region us-east-2

## Security Approach

The AWS deployment follows the same principles used throughout the homelab:

1. Inspect existing infrastructure before changing it.
2. Minimize exposed services.
3. Restrict SSH access to a known source IP.
4. Use key-based authentication.
5. Use IAM Identity Center instead of long-lived AWS access keys.
6. Enable host-level firewall protection.
7. Verify changes after implementation.
8. Document the infrastructure for repeatability.

## Next Steps

Planned AWS work:

- Install and configure AWS-focused tooling
- Explore EC2 administration
- Learn AWS networking concepts
- Introduce CloudWatch monitoring
- Practice S3
- Connect AWS concepts with Terraform
- Manage AWS infrastructure through Infrastructure as Code
- Add AWS automation to the existing homelab portfolio
