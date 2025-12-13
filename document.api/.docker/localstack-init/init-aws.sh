#!/bin/bash
echo "Initializing LocalStack S3..."
awslocal s3 mb s3://documents-bucket
echo "S3 Bucket 'documents-bucket' created."
