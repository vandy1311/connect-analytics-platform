"""Knowledge Base stack: S3 data source + Bedrock Knowledge Base.

Creates an S3 bucket for knowledge base documents (SOPs, compliance,
training materials) and a Bedrock Knowledge Base with vector embeddings
for retrieval-augmented generation (RAG).

For the hackathon, documents are uploaded from the local knowledge_base/
directory during deployment via a CDK custom resource.
"""

from aws_cdk import (
    CfnOutput,
    CfnResource,
    Duration,
    RemovalPolicy,
    Stack,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
)
from constructs import Construct


class KnowledgeBaseStack(Stack):
    """S3 + Bedrock Knowledge Base for agent RAG.

    Attributes:
        kb_bucket: S3 bucket holding knowledge base documents.
        knowledge_base_id: The Bedrock Knowledge Base ID (for agent config).
    """

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # ------------------------------------------------------------------
        # S3 Bucket for knowledge base documents
        # ------------------------------------------------------------------
        self.kb_bucket = s3.Bucket(
            self,
            "KnowledgeBaseBucket",
            bucket_name=f"connect-analytics-kb-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ------------------------------------------------------------------
        # Upload local knowledge_base/ docs to S3 on deploy
        # ------------------------------------------------------------------
        s3deploy.BucketDeployment(
            self,
            "UploadKBDocs",
            sources=[s3deploy.Source.asset("knowledge_base")],
            destination_bucket=self.kb_bucket,
            destination_key_prefix="documents/",
        )

        # ------------------------------------------------------------------
        # IAM Role for Bedrock Knowledge Base
        # ------------------------------------------------------------------
        kb_role = iam.Role(
            self,
            "KBRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Allows Bedrock Knowledge Base to read S3 documents",
        )
        self.kb_bucket.grant_read(kb_role)

        # Bedrock needs to invoke the embedding model
        kb_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=[
                    f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0"
                ],
            )
        )

        # ------------------------------------------------------------------
        # Bedrock Knowledge Base (CfnResource — no L2 construct yet)
        # ------------------------------------------------------------------
        self._knowledge_base = CfnResource(
            self,
            "BedrockKnowledgeBase",
            type="AWS::Bedrock::KnowledgeBase",
            properties={
                "Name": "connect-analytics-knowledge-base",
                "Description": (
                    "Contact center SOPs, compliance checklists, and training "
                    "materials for agent RAG enrichment."
                ),
                "RoleArn": kb_role.role_arn,
                "KnowledgeBaseConfiguration": {
                    "Type": "VECTOR",
                    "VectorKnowledgeBaseConfiguration": {
                        "EmbeddingModelArn": (
                            f"arn:aws:bedrock:{self.region}::foundation-model/"
                            "amazon.titan-embed-text-v2:0"
                        ),
                    },
                },
                "StorageConfiguration": {
                    "Type": "OPENSEARCH_SERVERLESS",
                    "OpensearchServerlessConfiguration": {
                        "CollectionArn": "TBD",  # Created automatically by Bedrock
                        "FieldMapping": {
                            "MetadataField": "metadata",
                            "TextField": "text",
                            "VectorField": "vector",
                        },
                    },
                },
            },
        )

        # ------------------------------------------------------------------
        # Data Source — S3 bucket
        # ------------------------------------------------------------------
        CfnResource(
            self,
            "KBDataSource",
            type="AWS::Bedrock::DataSource",
            properties={
                "KnowledgeBaseId": self._knowledge_base.ref,
                "Name": "connect-analytics-docs",
                "Description": "SOPs, compliance, and training documents from S3",
                "DataSourceConfiguration": {
                    "Type": "S3",
                    "S3Configuration": {
                        "BucketArn": self.kb_bucket.bucket_arn,
                        "InclusionPrefixes": ["documents/"],
                    },
                },
            },
        )

        # ------------------------------------------------------------------
        # Outputs
        # ------------------------------------------------------------------
        self.knowledge_base_id = self._knowledge_base.ref

        CfnOutput(
            self,
            "KnowledgeBaseId",
            value=self._knowledge_base.ref,
            description="Bedrock Knowledge Base ID for agent configuration",
        )
        CfnOutput(
            self,
            "KBBucketName",
            value=self.kb_bucket.bucket_name,
            description="S3 bucket containing knowledge base documents",
        )
