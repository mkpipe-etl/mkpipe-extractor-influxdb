from typing import Optional

from mkpipe.spark.base import BaseExtractor
from mkpipe.models import ConnectionConfig, ExtractResult, TableConfig
from mkpipe.utils import get_logger

logger = get_logger(__name__)


class InfluxDBExtractor(BaseExtractor, variant='influxdb'):
    def __init__(self, connection: ConnectionConfig):
        self.connection = connection
        self.host = connection.host or 'localhost'
        self.port = connection.port or 8086
        self.token = connection.api_key or connection.oauth_token
        self.org = connection.extra.get('org', '')
        self.bucket = connection.database

    def extract(self, table: TableConfig, spark, last_point: Optional[str] = None) -> ExtractResult:
        logger.info({
            'table': table.target_name,
            'status': 'extracting',
            'replication_method': table.replication_method.value,
        })

        from influxdb_client import InfluxDBClient
        import pandas as pd

        url = f'http://{self.host}:{self.port}'
        client = InfluxDBClient(url=url, token=self.token, org=self.org)
        query_api = client.query_api()

        measurement = table.name

        if table.replication_method.value == 'incremental' and last_point:
            flux_query = (
                f'from(bucket: "{self.bucket}") '
                f'|> range(start: {last_point}) '
                f'|> filter(fn: (r) => r._measurement == "{measurement}")'
            )
            write_mode = 'append'
        else:
            flux_query = (
                f'from(bucket: "{self.bucket}") '
                f'|> range(start: -30d) '
                f'|> filter(fn: (r) => r._measurement == "{measurement}")'
            )
            write_mode = 'overwrite'

        tables = query_api.query(flux_query)
        client.close()

        records = []
        for t in tables:
            for record in t.records:
                row = {
                    '_time': str(record.get_time()),
                    '_measurement': record.get_measurement(),
                    '_field': record.get_field(),
                    '_value': record.get_value(),
                }
                for k, v in record.values.items():
                    if k not in ('_time', '_measurement', '_field', '_value', 'result', 'table', '_start', '_stop'):
                        row[k] = v
                records.append(row)

        if not records:
            logger.info({'table': table.target_name, 'status': 'extracted', 'rows': 0})
            return ExtractResult(df=None, write_mode=write_mode)

        pdf = pd.DataFrame(records)
        df = spark.createDataFrame(pdf)

        last_point_value = None
        if records:
            last_point_value = records[-1].get('_time')

        logger.info({
            'table': table.target_name,
            'status': 'extracted',
            'write_mode': write_mode,
            'rows': len(records),
        })

        return ExtractResult(df=df, write_mode=write_mode, last_point_value=last_point_value)
