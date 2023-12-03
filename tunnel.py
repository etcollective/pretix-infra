import pulumi
from pulumi_cloudflare import (
    get_zone,
    Record,
    Tunnel,
    TunnelConfig,
    TunnelConfigConfigArgs,
    TunnelConfigConfigIngressRuleArgs,
)
from pulumi_github import ActionsSecret
from pulumi_random import RandomId

from compute import config, instance
from db import repo

# Create DNS Record
dns = config.require('zone')
zone = get_zone(name=dns)
hostname = config.require('hostname')
url = f'{hostname}.{dns}'

# Generate Tunnel Secret
tunnel_secret = RandomId(
    'cloudflare-tunnel-secret',
    byte_length=64,
    opts=pulumi.ResourceOptions(parent=instance),
)

# Setup Tunnel
tunnel = Tunnel(
    'cloudflare-tunnel',
    account_id=zone.account_id,
    name='Pretix Tunnel',
    secret=tunnel_secret.b64_std,
    config_src='cloudflare',
    opts=pulumi.ResourceOptions(parent=instance),
)

tunnel_config = TunnelConfig(
    'cloudflare-tunnel-config',
    account_id=zone.account_id,
    tunnel_id=tunnel.id,
    config=TunnelConfigConfigArgs(
        ingress_rules=[
            TunnelConfigConfigIngressRuleArgs(
                service='http://localhost:8345',
                hostname=url,
            ),
            TunnelConfigConfigIngressRuleArgs(
                service='http_status:404',
                path='media/cachedfiles',
                hostname=url,
            ),
            TunnelConfigConfigIngressRuleArgs(
                service='http_status:404',
                path='media/invoices',
                hostname=url,
            ),
            TunnelConfigConfigIngressRuleArgs(
                service='http_status:404',
            ),
        ]
    ),
    opts=pulumi.ResourceOptions(parent=tunnel),
)

# dns_record = Record(
#     'pretix-dns-record',
#     zone_id=zone.id,
#     name=hostname,
#     type='CNAME',
#     proxied=True,
#     value=tunnel.id.apply(lambda id: f'{id}.cfargotunnel.com'),
#     comment='Managed by Pulumi',
#     opts=pulumi.ResourceOptions(
#         parent=tunnel,
#         depends_on=[instance, tunnel_secret, tunnel],
#         delete_before_replace=True,
#         deleted_with=tunnel,
#     ),
# )

tunnel_secret_gh = ActionsSecret(
    'cloudflare-tunnel-gh-secret',
    repository=repo,
    secret_name='CF_TUNNEL_TOKEN',
    plaintext_value=tunnel.tunnel_token,
    opts=pulumi.ResourceOptions(parent=tunnel_secret),
)
