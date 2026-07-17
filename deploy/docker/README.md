# Local development infrastructure

This Compose stack provides the shared local dependencies for CPMS and OSPS:

- PostgreSQL for CPMS persistence
- RabbitMQ with the management UI for CPMS/OSPS messaging
- Valkey for future CMP integration; CPMS/OSPS do not depend on it initially

All published ports bind to `127.0.0.1` and are not exposed to the LAN.

## Start

Optionally copy `.env.example` to `.env` and change the development passwords,
then run:

```powershell
docker compose up -d --wait
docker compose ps
```

Run the commands from this directory. RabbitMQ Management is available at
<http://127.0.0.1:15672>.

Default local connection values when no `.env` file is present:

```text
PostgreSQL: postgresql://cpms:cpms_dev_password@127.0.0.1:5432/cpms
RabbitMQ:   amqp://cmp:cmp_dev_password@127.0.0.1:5672/cmp
Valkey:     valkey://:valkey_dev_password@127.0.0.1:6379/0
```

CPMS runtime settings for the same stack:

```text
CPMS_ENVIRONMENT=development
CPMS_DATABASE_URL=postgresql+psycopg://cpms:cpms_dev_password@127.0.0.1:5432/cpms
CPMS_RABBITMQ_URL=amqp://cmp:cmp_dev_password@127.0.0.1:5672/cmp
```

CPMS readiness (`/health/ready`) depends on PostgreSQL and RabbitMQ only.
Valkey remains available for future CMP services and is not a CPMS readiness
dependency.

## Stop and reset

```powershell
docker compose down
docker compose down --volumes  # also deletes local development data
```
