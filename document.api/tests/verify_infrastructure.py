import boto3
import pyodbc
import requests
import os
import time

# Configuration (Defaults match .env.dev)
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

 00
S03_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "documents-bucket")

DB_SERVER = "localhost,1433"
DB_USER = "sa"
DB_PASSWORD = "documentPassword123!"
DB_NAME = "documentdb"

API_URL = "http://localhost:8000"


def check_localstack():
    print(f"\n[1/3] Checking LocalStack S3 at {AWS_ENDPOINT_URL}...")
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=AWS_ENDPOINT_URL,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
        )
        response = s3.list_buckets()
        buckets = [b["Name"] for b in response.get("Buckets", [])]
        print(f"   -> Connected! Buckets found: {buckets}")

        if S3_BUCKET_NAME in buckets:
            print(f"   -> Bucket '{S3_BUCKET_NAME}' exists ✅")
        else:
            print(
                f"   -> Bucket '{S3_BUCKET_NAME}' NOT found ❌. Creation script might have failed or not run yet."
            )
            # Optional: Try creating it
            # s3.create_bucket(Bucket=S3_BUCKET_NAME)
    except Exception as e:
        print(f"   -> Failed to connect to LocalStack: {e} ❌")


def check_mssql():
    print(f"\n[2/3] Checking SQL Server at {DB_SERVER}...")
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        f"TrustServerCertificate=yes;"
    )
    try:
        conn = pyodbc.connect(conn_str, timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        row = cursor.fetchone()
        print(f"   -> Connected! Version: {row[0].split()[0]} ... ✅")
        conn.close()
    except Exception as e:
        print(f"   -> Failed to connect to SQL Server: {e} ❌")


def check_api():
    print(f"\n[3/3] Checking API at {API_URL}...")
    try:
        response = requests.get(f"{API_URL}/docs", timeout=5)
        if response.status_code == 200:
            print(f"   -> API Docs accessible at {API_URL}/docs ✅")
        else:
            print(f"   -> API responded with {response.status_code} ⚠️")
    except Exception as e:
        print(f"   -> Failed to connect to API: {e} ❌")


if __name__ == "__main__":
    print("--- Starting Infrastructure Verification ---")
    check_localstack()
    check_mssql()
    check_api()
    print("\n--- Done ---")
