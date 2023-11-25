import pulumi
from pulumi_gcp import compute, oslogin

from iam import ansible_sa

# Setup Vars
config = pulumi.Config('compute')
disk_size = config.get('disk_size') or 20
machine_type = config.get('machine_type') or 'e2-small'
ssh_key = config.get('ssh-key')

# Get Subnet
subnet = compute.get_subnetwork(
    name='public-production-subnet',
    project='common-405623',
)

# Setup IP Reservation
public_ip = compute.Address(
    'vm-public-ip',
    name='pretix',
    network_tier='STANDARD',
    opts=pulumi.ResourceOptions(protect=True),
)
# Setup VM
instance = compute.Instance(
    'vm-instance',
    name='pretix-prod-1',
    machine_type=machine_type,
    boot_disk=compute.InstanceBootDiskArgs(
        initialize_params=compute.InstanceBootDiskInitializeParamsArgs(
            size=disk_size,
            image='debian-12',
            type='pd-balanced',
        ),
    ),
    network_interfaces=[
        compute.InstanceNetworkInterfaceArgs(
            subnetwork=subnet.self_link,
            access_configs=[
                compute.InstanceNetworkInterfaceAccessConfigArgs(
                    nat_ip=public_ip.address,
                )
            ],
        )
    ],
)
