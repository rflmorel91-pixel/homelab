#!/usr/bin/env python3
"""Explicit, isolated staging lifecycle. Never reads production .env."""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import subprocess

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / '.runtime'
ENV = {key: os.environ[key] for key in ('PATH', 'HOME', 'TERM') if key in os.environ}


def run(args, capture=True):
    result = subprocess.run(args, cwd=ROOT, env=ENV, text=True,
                            capture_output=capture, check=False)
    if result.returncode:
        # Compose diagnostic output can contain secrets: do not echo it.
        raise SystemExit(f'Command failed: {args[0]} (exit {result.returncode}). No secrets printed.')
    return result.stdout.strip() if capture else ''


def guard():
    repo = Path(run(['git', 'rev-parse', '--show-toplevel'])).resolve()
    if repo == (Path.home() / 'homelab').resolve():
        raise SystemExit('Refusing to operate from production checkout.')
    if run(['git', 'branch', '--show-current']) != 'infrastructure/isolated-staging':
        raise SystemExit('Use the dedicated infrastructure/isolated-staging worktree.')
    if ROOT != repo / 'saas/jobflow/staging':
        raise SystemExit('Unexpected staging directory.')


def compose(*args, capture=True):
    if not (RUNTIME / 'runtime.env').is_file():
        raise SystemExit('Initialize staging first.')
    return run(['docker-compose', '--project-name', 'fieldlookers-staging',
                '--env-file', str(RUNTIME / 'runtime.env'),
                '-f', str(ROOT / 'compose.yml'), *args], capture=capture)


def initialize():
    if RUNTIME.exists():
        raise SystemExit('Runtime directory already exists; refusing to overwrite keys or credentials.')
    images = {}
    for name, target in [('WEB', 'jobflow-web'), ('DB', 'jobflow-db')]:
        images[name] = run(['docker', 'inspect', '--format', '{{.Image}}', target])
    images['MAIL'] = run(['docker', 'image', 'inspect', '--format', '{{.Id}}', 'axllent/mailpit:latest'])
    if not all(re.fullmatch(r'sha256:[a-f0-9]{64}', image) for image in images.values()):
        raise SystemExit('Could not resolve exact local image IDs.')
    os.umask(0o077)
    RUNTIME.mkdir(mode=0o700)
    tls = RUNTIME / 'tls'; tls.mkdir(mode=0o700)
    lines = [f'STAGING_{name}_IMAGE={image}' for name, image in images.items()]
    lines += ['STAGING_DB_PASSWORD=' + secrets.token_hex(32),
              'STAGING_JWT_SECRET=' + secrets.token_hex(48)]
    (RUNTIME / 'runtime.env').write_text('\n'.join(lines) + '\n')
    # Certificates are created locally, not installed in any trust store.
    run(['openssl', 'req', '-x509', '-newkey', 'rsa:3072', '-noenc',
         '-days', '30', '-subj', '/CN=FieldLookers Staging Local CA',
         '-addext', 'basicConstraints=critical,CA:TRUE,pathlen:0',
         '-addext', 'keyUsage=critical,keyCertSign,cRLSign',
         '-keyout', str(tls / 'ca.key'), '-out', str(tls / 'ca.crt')])
    run(['openssl', 'req', '-new', '-newkey', 'rsa:2048', '-noenc',
         '-subj', '/CN=localhost', '-keyout', str(tls / 'server.key'),
         '-out', str(tls / 'server.csr')])
    (tls / 'server.ext').write_text(
        'basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\n'
        'extendedKeyUsage=serverAuth\nsubjectAltName=DNS:localhost,IP:127.0.0.1\n')
    run(['openssl', 'x509', '-req', '-in', str(tls / 'server.csr'),
         '-CA', str(tls / 'ca.crt'), '-CAkey', str(tls / 'ca.key'), '-CAcreateserial',
         '-days', '14', '-extfile', str(tls / 'server.ext'), '-out', str(tls / 'server.crt')])
    run(['openssl', 'verify', '-CAfile', str(tls / 'ca.crt'), str(tls / 'server.crt')])
    print('Local secrets and certificates created. No container started; no certificate trusted.')
    print('CA SHA-256 fingerprint:')
    print(run(['openssl', 'x509', '-in', str(tls / 'ca.crt'), '-noout', '-fingerprint', '-sha256']))


def validate():
    cfg = json.loads(compose('config', '--format', 'json'))
    require = lambda condition, message: condition or fail(message)
    require(cfg['name'] == 'fieldlookers-staging', 'project name')
    require(set(cfg['services']) == {'staging-db', 'staging-api', 'staging-migrate', 'staging-web', 'staging-mail', 'staging-private-storage-init'}, 'services')
    require(set(cfg['networks']) == {'isolated', 'ingress'}, 'network list')
    require(cfg['networks']['isolated'].get('internal') is True, 'network isolation')
    require(not cfg['networks']['ingress'].get('internal'), 'ingress network')
    for network in cfg['networks'].values():
        require(not network.get('external'), 'external network')
    for name, service in cfg['services'].items():
        require(not service.get('container_name'), 'fixed container name')
        expected_networks = {'isolated', 'ingress'} if name == 'staging-web' else {'isolated'}
        require(set(service['networks']) == expected_networks, 'service network')
        require(service.get('restart') == 'no', 'restart policy')
        require(service.get('mem_limit'), 'memory limit')
        require(not service.get('privileged') and not service.get('network_mode'), 'privileged/network mode')
        require(not service.get('env_file'), 'unexpected environment file')
        for port in service.get('ports', []):
            require(port.get('host_ip') == '127.0.0.1', 'non-loopback port')
        if name != 'staging-web':
            require(not service.get('ports'), 'backend/database published port')
        for mount in service.get('volumes', []):
            if mount['type'] == 'volume':
                allowed_volume = (
                    name == 'staging-db'
                    and mount['source'] == 'staging_database'
                    and mount['target'] == '/var/lib/postgresql/data'
                ) or (
                    name in {'staging-api', 'staging-private-storage-init'}
                    and mount['source'] == 'staging_private_documents'
                    and mount['target'] == '/var/lib/jobflow-private/prestamodesk'
                )
                require(allowed_volume, 'unexpected data volume')
            elif mount['type'] == 'bind':
                path = Path(mount['source']).resolve()
                require(path.is_relative_to(ROOT) or path == ROOT.parent / 'app', 'mount outside staging worktree')
                require(mount.get('read_only') is True, 'writable bind mount')
            else:
                fail('unexpected mount type')
    storage_init = cfg['services'].get('staging-private-storage-init')
    require(storage_init is not None, 'private storage initializer')
    require(storage_init.get('user') == '0:0', 'storage initializer user')
    require(storage_init.get('cap_drop') == ['ALL'], 'storage initializer capabilities')
    require(storage_init.get('cap_add') == ['CHOWN'], 'storage initializer capabilities')
    require(storage_init.get('security_opt') == ['no-new-privileges:true'], 'storage initializer security')
    require(storage_init.get('command') == ['chown', '-R', '10001:10001', '/var/lib/jobflow-private/prestamodesk'], 'storage initializer command')
    api_dependencies = cfg['services']['staging-api'].get('depends_on', {})
    require(api_dependencies.get('staging-private-storage-init', {}).get('condition') == 'service_completed_successfully', 'storage initializer dependency')
    for name in ('staging-api', 'staging-migrate'):
        require(cfg['services'][name].get('user') == '10001:10001', name + ' runtime user')
    require(cfg['services']['staging-api'].get('read_only') is True, 'API read-only root')
    require(set(cfg['services']['staging-api'].get('tmpfs', [])) == {'/tmp:rw,noexec,nosuid,size=64m,mode=1777'}, 'API tmpfs')
    require(cfg['services']['staging-web'].get('read_only') is True, 'web read-only root')
    require(set(cfg['services']['staging-web'].get('tmpfs', [])) == {
        '/run:rw,noexec,nosuid,size=16m,mode=0755',
        '/var/cache/nginx:rw,noexec,nosuid,size=64m,mode=0755',
    }, 'web tmpfs')
    for name in ('staging-api', 'staging-web', 'staging-mail'):
        service = cfg['services'][name]
        require(service.get('cap_drop') == ['ALL'], name + ' dropped capabilities')
        require(service.get('security_opt') == ['no-new-privileges:true'], name + ' no-new-privileges')
    require(cfg['services']['staging-web'].get('cap_add') == ['NET_BIND_SERVICE', 'DAC_OVERRIDE', 'SETUID', 'SETGID', 'CHOWN'], 'web capability allowlist')
    require(cfg['services']['staging-db'].get('read_only') is True, 'database read-only root')
    require(cfg['services']['staging-db'].get('security_opt') == ['no-new-privileges:true'], 'database no-new-privileges')
    require(set(cfg['services']['staging-db'].get('tmpfs', [])) == {
        '/tmp:rw,noexec,nosuid,size=64m,mode=1777',
        '/run/postgresql:rw,noexec,nosuid,size=16m,mode=3775',
    }, 'database tmpfs')
    web_build = cfg['services']['staging-web'].get('build', {})
    require(Path(web_build.get('context', '')).resolve() == ROOT / 'web-image', 'web build context')
    require(web_build.get('dockerfile') == 'Dockerfile', 'web Dockerfile path')
    web_recipe = (ROOT / 'web-image' / 'Dockerfile').read_text()
    require('FROM nginx@sha256:1ef7ca94d7879df82421428ce13bd1eaa412404953859cf7a5b6512c25e67a60' in web_recipe, 'pinned web base image')
    for package in ('brotli-libs=1.2.1-r0', 'curl=8.23.0-r0', 'libcurl=8.23.0-r0'):
        require(package in web_recipe, 'pinned web package')
    web_ports = cfg['services']['staging-web'].get('ports', [])
    require(len(web_ports) == 2 and {(str(p['published']), int(p['target'])) for p in web_ports} == {('18443', 443), ('18025', 8025)}, 'gateway ports')
    for name in ('staging-api', 'staging-migrate'):
        env = cfg['services'][name]['environment']
        require(env['FIELDLOOKERS_STAGING_ONLY'] == '1', 'staging flag')
        require('@staging-db:5432/fieldlookers_staging' in env['DATABASE_URL'], 'database URL')
        require(env['PLATFORM_PUBLIC_BASE_URL'] == 'https://localhost:8443', 'public URL')
        require(env['OPENAI_API_KEY'] == '', 'external API key')
        for prefix in ('PLATFORM', 'RENEWALDESK'):
            require(env[prefix + '_SMTP_HOST'] == 'staging-mail', 'email destination')
            require(env[prefix + '_SMTP_PASSWORD'] == '', 'SMTP credentials')
    require(set(cfg['volumes']) == {'staging_database', 'staging_private_documents'}, 'volume list')
    for volume in cfg['volumes'].values():
        require(not volume.get('external'), 'external volume')
    require(cfg['volumes']['staging_database']['name'] == 'fieldlookers-staging_isolated_staging_database', 'database volume identity')
    require(cfg['volumes']['staging_private_documents']['name'] == 'fieldlookers-staging_staging_private_documents', 'private documents volume identity')
    print('STAGING CONFIG VALIDATED: separate services, database, loopback ports, internal network and test email.')
    print('Runtime connectivity, TLS, email capture and browser behavior still require verification.')


def fail(message):
    raise SystemExit('Unsafe staging configuration: ' + message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'validate', 'build', 'start', 'status', 'stop', 'seed-admin'])
    action = parser.parse_args().action
    guard()
    if action == 'init':
        initialize(); return
    validate()
    if action == 'build':
        compose('build', 'staging-api', 'staging-web', capture=False)
    elif action == 'start':
        compose('up', '-d', '--no-build', '--pull', 'never', capture=False)
    elif action == 'status':
        compose('ps', '-a', capture=False)
    elif action == 'stop':
        compose('stop', capture=False)
    elif action == 'seed-admin':
        compose('exec', 'staging-api', 'python', '/staging/bootstrap_admin.py', capture=False)


if __name__ == '__main__':
    main()
