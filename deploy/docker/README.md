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

## Stop and reset

```powershell
docker compose down
docker compose down --volumes  # also deletes local development data
```
