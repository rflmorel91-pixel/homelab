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

## Cost Management

A monthly AWS Budget was created to provide cost visibility and spending alerts for the homelab environment.

| Setting | Configuration |
|---|---|
| Budget Name | homelab-monthly-budget |
| Monthly Limit | $10 USD |
| Alert Type | Actual spending |
| Alert Threshold | 80% |
| Notification | Email |
| Email | rflmorel91@gmail.com |

The budget provides an early warning for AWS spending. It does not enforce a hard spending limit.

The budget was verified using the AWS CLI:

```bash
aws budgets describe-budgets \
  --profile rafael-aws \
  --account-id 723681698511
```

The notification subscriber was also verified through the AWS Budgets API.

## CloudWatch Monitoring

Amazon CloudWatch monitoring was verified for the EC2 instance `i-0656dad4a272bef78`.

Available EC2 metrics include:

- CPU utilization
- Network traffic
- EBS activity
- CPU credit usage
- EC2 status checks
- Instance and system health indicators

### Monitoring Baseline

The initial CloudWatch baseline showed:

| Metric | Result |
|---|---|
| CPU Utilization | Very low / idle |
| StatusCheckFailed | 0 |
| NetworkIn | Low traffic |
| NetworkOut | Low traffic |

CloudWatch metric queries were performed using the AWS CLI with the `rafael-aws` SSO profile.

Example:

```bash
aws cloudwatch get-metric-statistics \
  --profile rafael-aws \
  --region us-east-2 \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-0656dad4a272bef78
```

This establishes an initial monitoring baseline that can later be extended with CloudWatch alarms, dashboards, and automated alerting.

## EBS Encryption

The initial EC2 storage audit found that EBS encryption by default was disabled in `us-east-2`.

The EC2 root volume was also identified as unencrypted:

| Setting | Value |
|---|---|
| Root Volume | `vol-0c36c7f2f48091efc` |
| Size | 8 GiB |
| Type | gp3 |
| Encryption | Not encrypted |

EBS encryption by default was then enabled for the `us-east-2` region.

Verification:

```bash
aws ec2 get-ebs-encryption-by-default \
  --profile rafael-aws \
  --region us-east-2

True
```

Enabling encryption by default protects future EBS volumes. The existing root volume remains unencrypted and is documented as a future hardening item.

## Security Baseline Verification

The final AWS EC2 security baseline was verified after implementing the initial hardening controls.

| Control | Result |
|---|---|
| Security Group SSH | TCP 22 from `69.127.140.117/32` only |
| UFW | Active |
| UFW Incoming | Deny by default |
| UFW Outgoing | Allow by default |
| UFW SSH | TCP 22 from `69.127.140.117` only |
| IMDSv2 | Required |
| IAM Instance Profile | None |
| EBS Encryption by Default | Enabled |
| Root EBS Volume | Existing volume remains unencrypted |

The AWS Security Group and Ubuntu UFW provide layered protection for SSH access.

The EC2 instance was also verified as running and reachable through SSH after the firewall configuration was applied.

## Backup and Recovery

An EBS snapshot was created to establish an initial backup and recovery baseline for the AWS EC2 environment.

| Setting | Value |
|---|---|
| Source Volume | `vol-0c36c7f2f48091efc` |
| Snapshot | `snap-011c02daa1d796d81` |
| Snapshot State | Completed |
| Progress | 100% |
| Size | 8 GiB |
| Encryption | Not encrypted |
| Description | Homelab AWS root volume backup |
| Name Tag | `homelab-aws-root-backup` |
| Project Tag | `90-day-it-program` |
| Environment Tag | `homelab` |
| Managed By | `manual` |

The snapshot was verified through the AWS CLI after creation and reached a completed state.

Because the existing root EBS volume is unencrypted, this snapshot is also unencrypted. EBS encryption by default is enabled for future volumes, while migration of the existing root volume remains a future hardening and recovery exercise.

Future backup work can include automated snapshot policies, retention management, encrypted backup copies, and restoration testing.

### Backup Verification

The completed snapshot was independently verified after creation.

The backup chain was confirmed as:

- EC2 instance: `i-0656dad4a272bef78`
- Root volume: `vol-0c36c7f2f48091efc`
- Snapshot: `snap-011c02daa1d796d81`

The snapshot reached `completed` state with `100%` progress and remains available in the standard EBS snapshot storage tier.

The source root volume remains attached to the running EC2 instance as `/dev/sda1`.

No restoration or replacement of the production root volume was performed during this exercise.

## CloudWatch Alarms

A CloudWatch CPU utilization alarm was configured for the AWS EC2 instance.

| Setting | Value |
|---|---|
| Alarm | `homelab-aws-ec2-high-cpu` |
| Instance | `i-0656dad4a272bef78` |
| Metric | `CPUUtilization` |
| Statistic | Average |
| Period | 300 seconds |
| Evaluation Periods | 2 |
| Threshold | 80% |
| Condition | Greater Than |
| Actions | SNS notification enabled |

The alarm was verified through the AWS CLI and transitioned to `OK` after CloudWatch evaluated two consecutive datapoints below the 80% threshold.

The alarm currently provides monitoring and state evaluation with SNS email notification actions enabled. Future improvements can include additional health alarms, CloudWatch dashboards, and automated incident response.

### EC2 Status Check Alarm

A second CloudWatch alarm was configured to monitor EC2 instance status checks.

| Setting | Value |
|---|---|
| Alarm | `homelab-aws-ec2-status-check` |
| Instance | `i-0656dad4a272bef78` |
| Metric | `StatusCheckFailed` |
| Statistic | Maximum |
| Period | 300 seconds |
| Evaluation Periods | 1 |
| Threshold | Greater Than 0 |
| Actions | None configured |

The alarm was verified through the AWS CLI and transitioned to `OK` after CloudWatch evaluated a `0.0` datapoint, confirming that no EC2 status-check failures were detected.

Together, the CPU utilization and status-check alarms provide an initial CloudWatch monitoring baseline for the AWS EC2 instance.

### SNS Alerting

Amazon SNS was configured to provide email notifications for CloudWatch alarm events.

| Setting | Value |
|---|---|
| Topic | `homelab-aws-alerts` |
| Region | `us-east-2` |
| Protocol | Email |
| Subscription | Confirmed |
| CPU Alarm | SNS notification enabled |
| Status Check Alarm | SNS notification enabled |
| Alarm Actions | Enabled |

The SNS notification path was tested independently using the AWS CLI. A test message was successfully published to the topic and received by the subscribed email address.

The resulting monitoring and alerting workflow is:

`EC2 → CloudWatch → Alarm → SNS → Email`

No automated remediation actions are configured. Future improvements can include additional CloudWatch alarms, SNS integrations, dashboards, and automated incident response.

### AWS Backup

AWS Backup was configured to protect the homelab EC2 instance using a dedicated backup vault and daily backup plan.

| Setting | Value |
|---|---|
| Backup Vault | `homelab-aws-vault` |
| Region | `us-east-2` |
| Backup Plan | `homelab-aws-daily` |
| Schedule | Daily at 05:00 UTC |
| Retention | 7 days |
| Resource Selection | `Project=90-day-it-program` |
| Protected Resource | `homelab-aws-01` |
| Backup Type | EC2 |
| Recovery Point | `ami-0cfd2bb6e34c12fbf` |
| Recovery Point Status | `COMPLETED` |

EC2 was explicitly enabled for AWS Backup in the `us-east-2` region. A tag-based backup selection was configured so resources tagged with `Project=90-day-it-program` are automatically selected by the backup plan.

An on-demand EC2 backup was successfully executed using AWS Backup. The backup job transitioned to `COMPLETED` and produced a completed recovery point in the `homelab-aws-vault` backup vault.

The verified workflow is:

`EC2 → AWS Backup → Backup Vault → Recovery Point`

The backup plan retains recovery points for 7 days. A restore operation was successfully tested and validated. Future improvements can include cross-region backup, additional protected resources, backup notifications, and automated recovery procedures.

### Backup Restore Validation

A full restore test was performed using the completed recovery point `ami-0cfd2bb6e34c12fbf`.

The restore job completed successfully and created a new EC2 instance:

| Setting | Value |
|---|---|
| Restore Job | `59442ea3-18d7-47ab-ada3-662e4494750d` |
| Recovery Point | `ami-0cfd2bb6e34c12fbf` |
| Restored Instance | `i-0600319d1b14f60c5` |
| Instance Type | `t3.micro` |
| Restore Status | `COMPLETED` |
| Validation Status | Instance reached `running` state |
| Cleanup Status | Restored test instance terminated |

The restored instance was verified in `us-east-2a` using the original VPC, subnet, security group, and SSH key configuration. The restored instance successfully entered the `running` state and was then terminated after validation to avoid unnecessary resource usage.

This confirms that the AWS Backup recovery point can be used to restore the protected EC2 workload successfully.

The verified disaster-recovery workflow is:

`EC2 → AWS Backup → Recovery Point → Restore → Running EC2 → Validation → Cleanup`

No production restore was required. The restore was performed against the completed recovery point as a controlled disaster-recovery validation exercise.
