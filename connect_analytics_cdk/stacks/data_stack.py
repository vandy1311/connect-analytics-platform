"""Data Foundation stack: S3 bucket, Glue Data Catalog, and Athena workgroup.

Creates the shared data lake infrastructure used by all three analytics agents.
- S3 bucket with prefix structure for CTR, Agent Events, and Contact Lens data
- Glue database and table definitions (via GlueTables construct)
- Athena workgroup with query result location
"""

from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_athena as athena,
    aws_glue as glue,
    aws_s3 as s3,
)
from constructs import Construct

from connect_analytics_cdk.glue_tables import GlueTables


class DataStack(Stack):
    """S3 + Glue Data Catalog + Athena workgroup for Connect analytics data.

    Attributes:
        data_bucket: The S3 bucket holding all Connect analytics data.
        glue_database: The Glue CfnDatabase resource.
        glue_tables: The GlueTables construct with CTR, Agent Events, and Contact Lens tables.
        athena_workgroup: The Athena workgroup for running queries.
    """

    def __init__(self, scope: Construct, id: str, *, bucket_name: str | None = None, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # ------------------------------------------------------------------
        # S3 Bucket — use provided name or default
        # ------------------------------------------------------------------
        self.data_bucket = s3.Bucket(
            self,
            "DataBucket",
            bucket_name=bucket_name or f"connect-analytics-{self.account}-{self.region}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ------------------------------------------------------------------
        # Glue Database — connect_analytics
        # ------------------------------------------------------------------
        self.glue_database = glue.CfnDatabase(
            self,
            "GlueDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name="connect_analytics",
                description="Connect Analytics Platform data catalog",
            ),
        )

        # ------------------------------------------------------------------
        # Glue Tables (CTR, Agent Events, Contact Lens)
        # ------------------------------------------------------------------
        self.glue_tables = GlueTables(
            self,
            "GlueTables",
            database=self.glue_database,
            data_bucket=self.data_bucket,
        )

        # ------------------------------------------------------------------
        # Athena Workgroup — connect-analytics
        # Query results stored under s3://<bucket>/athena-results/
        # ------------------------------------------------------------------
        self.athena_workgroup = athena.CfnWorkGroup(
            self,
            "AthenaWorkgroup",
            name="connect-analytics",
            description="Workgroup for Connect Analytics Platform queries",
            state="ENABLED",
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=f"s3://{self.data_bucket.bucket_name}/athena-results/",
                ),
                enforce_work_group_configuration=True,
            ),
        )
