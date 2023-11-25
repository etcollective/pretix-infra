import pulumi
from pulumi_gcp import compute

# Setup Vars
config = pulumi.Config('compute')
disk_size = config.get('disk_size') or 20
machine_type = config.get('machine_type') or 'e2-small'

# Get Subnet
subnet = compute.get_subnetwork(
    name='public-production-subnet',
    project='common-405623',
)

# Setup VM
instance = compute.Instance(
    'vm-instance',
    name='pretix-prod-1',
    machine_type=machine_type,
    boot_disk=compute.InstanceBootDiskArgs(
        initialize_params=compute.InstanceBootDiskInitializeParamsArgs(
            size=disk_size,
            image='rocky-linux-9-optimized-gcp',
            type='pd-balanced',
        ),
    ),
    network_interfaces=[
        compute.InstanceNetworkInterfaceArgs(subnetwork=subnet.self_link)
    ],
)
