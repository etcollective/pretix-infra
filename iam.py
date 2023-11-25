import pulumi
import pulumi_gcp as gcp

# Setup Ansible Service Account
ansible_sa = gcp.serviceaccount.Account(
    'ansible-sa',
    account_id='ansible',
    display_name='ansible',
    project='pretix-prod',
    opts=pulumi.ResourceOptions(protect=True),
)
