# mkpipe-extractor-influxdb

InfluxDB extractor plugin for [MkPipe](https://github.com/mkpipe-etl/mkpipe). Reads InfluxDB measurements using `influxdb-client` Flux queries and converts to Spark DataFrames.

## Documentation

For more detailed documentation, please visit the [GitHub repository](https://github.com/mkpipe-etl/mkpipe).

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

---

## Connection Configuration

```yaml
connections:
  influxdb_source:
    variant: influxdb
    host: localhost
    port: 8086
    database: my_bucket
    api_key: my-influx-token
    extra:
      org: my-org
```

---

## Table Configuration

The `name` field corresponds to the InfluxDB measurement name:

```yaml
pipelines:
  - name: influxdb_to_pg
    source: influxdb_source
    destination: pg_target
    tables:
      - name: cpu_usage
        target_name: stg_cpu_usage
        replication_method: full
```

### Incremental Replication

Incremental replication uses the last extracted `_time` value as the Flux `range(start:)` parameter:

```yaml
      - name: cpu_usage
        target_name: stg_cpu_usage
        replication_method: incremental
        iterate_column: _time
```

> **Note:** For full replication the default time range is `last 30 days`. Adjust with a `custom_query` if needed.

### Custom Flux Query

Use `custom_query` to override the generated Flux query entirely:

```yaml
      - name: cpu_usage
        target_name: stg_cpu_usage
        replication_method: full
        custom_query: |
          from(bucket: "my_bucket")
            |> range(start: -90d)
            |> filter(fn: (r) => r._measurement == "cpu_usage")
            |> filter(fn: (r) => r.host == "server01")
```

---

## Performance Notes

- InfluxDB query results are fetched synchronously on the Spark driver via the Flux API and then converted to a Spark DataFrame.
- For large time-series datasets, use incremental replication to limit the query window.
- The `fetchsize` parameter has no effect on this connector (Flux queries return complete results).
- Parallelism is not applicable here — the Flux API does not support sliced/parallel reads.

---

## All Table Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | string | required | InfluxDB measurement name |
| `target_name` | string | required | Destination table name |
| `replication_method` | `full` / `incremental` | `full` | `full` queries last 30d; `incremental` uses last `_time` |
| `iterate_column` | string | — | Should be `_time` for incremental |
| `custom_query` | string | — | Override the generated Flux query entirely |
| `tags` | list | `[]` | Tags for selective pipeline execution |
| `pass_on_error` | bool | `false` | Skip table on error instead of failing |

### Extra Connection Parameters

| Key | Default | Description |
|---|---|---|
| `org` | `""` | InfluxDB organization name |
