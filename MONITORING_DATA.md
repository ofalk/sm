# Monitoring Data Contract

This document describes the fields and data SM exposes to the monitoring
coverage exporter and sync controller.

## Stable names (`sm_name`)

| `sm_kind`        | `sm_name`               | Example                                |
| ---------------- | ----------------------- | -------------------------------------- |
| `server`         | `<hostname>.<domain>`   | `knode03.localghost.com`               |
| `clusterpackage` | `<cluster_name>/<name>` | `k.localghost.com/central-postgres-rw` |
| `domain`         | `<name>`                | `git.linux-kernel.de`                  |

The API exposes the computed `sm_name` as a read-only field on servers,
cluster packages and domains.

## Fields

### Server

- `monitoring` (API alias for `monitoring_from_puppet`, Boolean)
- `monitoring_profile` (`none`, `linux-basic`, `k8s-node`, `http-only`, `custom`)
- `criticality` (`critical`, `high`, `normal`, `low`)
- `owner_team` (string)
- `runbook_url` (URL)
- `monitoring_labels` (JSON object with extra Prometheus labels)
- `exporter_endpoints` (JSON object, e.g. `{"node_exporter": 9100}`)
- `maintenance_window` (human-readable string)

### Cluster

- `monitoring` (Boolean, default `true`)
- `sm_name` is the cluster name via the `name` field.

### ClusterPackage

- `monitoring` (Boolean, default `true`)
- `protocol` (`http`, `https`, `tcp`, `postgres`, `dns`)
- `check_path` (e.g. `/`, `/-/readiness`)
- `expected_status` (e.g. `200,301,302,401`)
- `tls_sni`
- `check_module` (Blackbox module, e.g. `http_2xx`)
- `metrics_host`, `metrics_port`
- `runbook_url`

`status_name` remains available as a read-only API field.

### Domain

- `monitoring` (Boolean)
- `check_http`, `check_tls` (Boolean)
- `expected_status`
- `tls_sni`

## Data quality command

The exporter needs active `In use` servers to have monitoring enabled and
monitored packages to be in the `In use` status.

```bash
# Report only
python manage.py monitoring_data_quality

# Apply safe normalisations
python manage.py monitoring_data_quality --apply

# Apply server flags but leave package statuses alone
python manage.py monitoring_data_quality --apply --skip-status
```

The command also reports duplicate FQDNs across tenant groups. It intentionally
does not resolve them automatically, because choosing which tenant keeps the
name is an operational decision.

## API key visibility

API keys inherit the owning user's group visibility. For the exporter to read
every tenant, create its key for a superuser or for a user that belongs to all
groups. Keys never bypass the per-object permission checks.

## Secrets and alert rules

SM stores no passwords, tokens or secrets for monitored endpoints; only an
external `secret_ref` belongs in this layer. PromQL rules and alert texts stay
in Git and are not managed by SM.
