import pulumi
from pulumi_gcp import compute, secretmanager, sql
from pulumi_github import ActionsSecret, ActionsVariable
from pulumi_random import RandomPassword

# Setup Vars
config = pulumi.Config()
gcp_config = pulumi.Config('gcp')
region = gcp_config.require('region')

# Setup Network
network = compute.get_network(name='production-vpc', project='common-405623')

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
            ipv4_enabled=False,
            private_network=network.id,
            require_ssl=True,
        ),
        insights_config=sql.DatabaseInstanceSettingsInsightsConfigArgs(
            query_insights_enabled=True,
            query_plans_per_minute=5,
            query_string_length=1024,
            record_application_tags=True,
            record_client_address=True,
        ),
    ),
    deletion_protection=False,
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

# Export values to Github Actions
repo = config.require('ansible-repo')

db_name = ActionsVariable(
    'db-name-gh-var',
    repository=repo,
    variable_name='PRETIX_DB_NAME',
    value=database.name,
    opts=pulumi.ResourceOptions(parent=database),
)

db_user = ActionsVariable(
    'db-user-gh-var',
    repository=repo,
    variable_name='PRETIX_DB_USER',
    value=user.name,
    opts=pulumi.ResourceOptions(parent=user),
)

db_password = ActionsSecret(
    'db-password-gh-secret',
    repository=repo,
    secret_name='PRETIX_DB_PASSWORD',
    plaintext_value=password.result,
    opts=pulumi.ResourceOptions(parent=password),
)
db_host = ActionsVariable(
    'db-host-gh-var',
    repository=repo,
    variable_name='PRETIX_DB_HOST',
    value=instance.private_ip_address,
    opts=pulumi.ResourceOptions(parent=instance),
)

# Setup Outputs
pulumi.export('db_connection_name', instance.connection_name)
pulumi.export('db_username', user.name)
pulumi.export('db_password', password.result)
pulumi.export('db_secret_version', version.id)
