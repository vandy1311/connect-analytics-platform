"""Glue Data Catalog table definitions for Connect Analytics Platform.

Defines three tables:
- connect_ctr: Contact Trace Records (Parquet)
- connect_agent_events: Agent Event stream data (Parquet)
- connect_contact_lens: Contact Lens analysis outputs (JSON)

All tables use year/month/day partition keys with partition projection
for automatic partition discovery (no Glue Crawlers needed).
"""

from constructs import Construct
from aws_cdk import (
    aws_glue as glue,
    aws_s3 as s3,
)


class GlueTables(Construct):
    """CDK construct that creates Glue Data Catalog tables for Connect data.

    Args:
        scope: CDK construct scope.
        id: Construct ID.
        database: The Glue database to create tables in.
        data_bucket: The S3 bucket containing the data.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        database: glue.CfnDatabase,
        data_bucket: s3.IBucket,
    ) -> None:
        super().__init__(scope, id)

        self._database = database
        self._data_bucket = data_bucket

        database_name = database.database_input.name

        self.ctr_table = self._create_ctr_table(database_name)
        self.agent_events_table = self._create_agent_events_table(database_name)
        self.contact_lens_table = self._create_contact_lens_table(database_name)

    def _partition_keys(self) -> list[glue.CfnTable.ColumnProperty]:
        """Common year/month/day partition keys for all tables."""
        return [
            glue.CfnTable.ColumnProperty(name="year", type="string"),
            glue.CfnTable.ColumnProperty(name="month", type="string"),
            glue.CfnTable.ColumnProperty(name="day", type="string"),
        ]

    def _partition_projection_params(self) -> dict[str, str]:
        """Partition projection parameters for automatic partition discovery.

        Uses date-based projection so Athena can resolve partitions without
        a Glue Crawler. Covers 2024-01-01 through 2026-12-31.
        """
        return {
            "projection.enabled": "true",
            "projection.year.type": "integer",
            "projection.year.range": "2024,2026",
            "projection.month.type": "integer",
            "projection.month.range": "1,12",
            "projection.month.digits": "2",
            "projection.day.type": "integer",
            "projection.day.range": "1,31",
            "projection.day.digits": "2",
            "storage.location.template": (
                "s3://${bucket}/${prefix}/year=${year}/month=${month}/day=${day}"
            ),
        }

    def _create_ctr_table(self, database_name: str) -> glue.CfnTable:
        """Create the connect_ctr table (Parquet format).

        Stores Contact Trace Records with queue, agent, timing, and outcome data.
        """
        s3_location = (
            f"s3://{self._data_bucket.bucket_name}/ctr/"
        )

        projection_params = self._partition_projection_params()
        projection_params["storage.location.template"] = (
            f"s3://{self._data_bucket.bucket_name}/ctr/"
            "year=${year}/month=${month}/day=${day}"
        )

        columns = [
            glue.CfnTable.ColumnProperty(name="contact_id", type="string"),
            glue.CfnTable.ColumnProperty(name="queue_name", type="string"),
            glue.CfnTable.ColumnProperty(name="agent_id", type="string"),
            glue.CfnTable.ColumnProperty(name="initiation_timestamp", type="timestamp"),
            glue.CfnTable.ColumnProperty(name="connected_timestamp", type="timestamp"),
            glue.CfnTable.ColumnProperty(name="disconnect_timestamp", type="timestamp"),
            glue.CfnTable.ColumnProperty(name="queue_duration_seconds", type="int"),
            glue.CfnTable.ColumnProperty(name="handle_time_seconds", type="int"),
            glue.CfnTable.ColumnProperty(name="outcome", type="string"),
            glue.CfnTable.ColumnProperty(name="service_level_met", type="boolean"),
        ]

        return glue.CfnTable(
            self,
            "ConnectCtrTable",
            catalog_id=self._database.catalog_id,
            database_name=database_name,
            table_input=glue.CfnTable.TableInputProperty(
                name="connect_ctr",
                table_type="EXTERNAL_TABLE",
                parameters=projection_params,
                partition_keys=self._partition_keys(),
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    columns=columns,
                    location=s3_location,
                    input_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe",
                    ),
                ),
            ),
        )

    def _create_agent_events_table(self, database_name: str) -> glue.CfnTable:
        """Create the connect_agent_events table (Parquet format).

        Stores Agent Event stream data with state, occupancy, and contact metrics.
        """
        s3_location = (
            f"s3://{self._data_bucket.bucket_name}/agent-events/"
        )

        projection_params = self._partition_projection_params()
        projection_params["storage.location.template"] = (
            f"s3://{self._data_bucket.bucket_name}/agent-events/"
            "year=${year}/month=${month}/day=${day}"
        )

        columns = [
            glue.CfnTable.ColumnProperty(name="event_id", type="string"),
            glue.CfnTable.ColumnProperty(name="agent_id", type="string"),
            glue.CfnTable.ColumnProperty(name="agent_name", type="string"),
            glue.CfnTable.ColumnProperty(name="event_type", type="string"),
            glue.CfnTable.ColumnProperty(name="current_state", type="string"),
            glue.CfnTable.ColumnProperty(name="state_start_timestamp", type="timestamp"),
            glue.CfnTable.ColumnProperty(name="state_duration_seconds", type="int"),
            glue.CfnTable.ColumnProperty(name="contacts_handled_today", type="int"),
            glue.CfnTable.ColumnProperty(name="occupancy_rate", type="float"),
        ]

        return glue.CfnTable(
            self,
            "ConnectAgentEventsTable",
            catalog_id=self._database.catalog_id,
            database_name=database_name,
            table_input=glue.CfnTable.TableInputProperty(
                name="connect_agent_events",
                table_type="EXTERNAL_TABLE",
                parameters=projection_params,
                partition_keys=self._partition_keys(),
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    columns=columns,
                    location=s3_location,
                    input_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe",
                    ),
                ),
            ),
        )

    def _create_contact_lens_table(self, database_name: str) -> glue.CfnTable:
        """Create the connect_contact_lens table (JSON format).

        Stores Contact Lens analysis outputs with sentiment, categories,
        transcripts, and compliance flags.
        """
        s3_location = (
            f"s3://{self._data_bucket.bucket_name}/contact-lens/"
        )

        projection_params = self._partition_projection_params()
        projection_params["storage.location.template"] = (
            f"s3://{self._data_bucket.bucket_name}/contact-lens/"
            "year=${year}/month=${month}/day=${day}"
        )

        columns = [
            glue.CfnTable.ColumnProperty(name="contact_id", type="string"),
            glue.CfnTable.ColumnProperty(name="agent_id", type="string"),
            glue.CfnTable.ColumnProperty(name="overall_sentiment", type="string"),
            glue.CfnTable.ColumnProperty(name="customer_sentiment_score", type="float"),
            glue.CfnTable.ColumnProperty(name="agent_sentiment_score", type="float"),
            glue.CfnTable.ColumnProperty(name="categories", type="array<string>"),
            glue.CfnTable.ColumnProperty(name="transcript_excerpt", type="string"),
            glue.CfnTable.ColumnProperty(name="compliance_flags", type="array<string>"),
            glue.CfnTable.ColumnProperty(name="analysis_timestamp", type="timestamp"),
        ]

        return glue.CfnTable(
            self,
            "ConnectContactLensTable",
            catalog_id=self._database.catalog_id,
            database_name=database_name,
            table_input=glue.CfnTable.TableInputProperty(
                name="connect_contact_lens",
                table_type="EXTERNAL_TABLE",
                parameters=projection_params,
                partition_keys=self._partition_keys(),
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    columns=columns,
                    location=s3_location,
                    input_format="org.apache.hadoop.mapred.TextInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.openx.data.jsonserde.JsonSerDe",
                    ),
                ),
            ),
        )
