import pulumi
from pulumi_gcp import sql, secretmanager
from pulumi_random import RandomPassword

# Setup Vars
gcp_config = pulumi.Config('gcp')
region = gcp_config.require('region')

# Setup Labels
labels = {
    'app': 'pretix',
    'env': 'prod',
    'component': 'database',
}

# Prepare Database Password
password = RandomPassword(
    'database-password-generation', length=16, special=True
)
secret = secretmanager.Secret(
    'database-password',
    labels=labels,
    secret_id='pretix-db-pw',
    replication=secretmanager.SecretReplicationArgs(
        user_managed=secretmanager.SecretReplicationUserManagedArgs(
            replicas=[
                secretmanager.SecretReplicationUserManagedReplicaArgs(
                    location=region,
                ),
            ],
        ),
    ),
    opts=(pulumi.ResourceOptions(parent=password, delete_before_replace=True)),
)

version = secretmanager.SecretVersion(
    'database-password-version',
    secret=secret.id,
    secret_data=password.result,
    opts=pulumi.ResourceOptions(parent=secret),
)

# Setup DB Instance
instance = sql.DatabaseInstance(
    'database-instance',
    database_version='POSTGRES_15',
    settings=sql.DatabaseInstanceSettingsArgs(
        tier='db-f1-micro',
        user_labels=labels,
        ip_configuration=sql.DatabaseInstanceSettingsIpConfigurationArgs(
            ipv4_enabled=True,
        ),
    ),
)

# Setup Database
database = sql.Database(
    'database',
    name='pretix',
    instance=instance.name,
    opts=pulumi.ResourceOptions(parent=instance),
)

# Setup Database User
user = sql.User(
    'database-user',
    name='pretixdbuser',
    instance=instance.name,
    password=password.result,
    opts=pulumi.ResourceOptions(parent=database),
)

# Export the connection string for the database
pulumi.export('db_connection_name', instance.connection_name)
pulumi.export('db_username', user.name)
pulumi.export('db_password', password.result)
pulumi.export('db_secret_version', version.id)
