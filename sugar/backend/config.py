import os
from pathlib import Path
from dotenv import load_dotenv

# Try to load environment variables from .env file
env_path = Path(__file__).parents[2] / '.env'
print(f"Looking for .env file at: {env_path}")
if env_path.exists():
    print("Found .env file, loading environment variables...")
    load_dotenv(env_path)
else:
    print("No .env file found")

# Database configurations
CLICKHOUSE_CONFIG = {
    'host': os.getenv('CLICKHOUSE_HOST'),
    'port': int(os.getenv('CLICKHOUSE_PORT', 8123)),  # HTTP interface
    'user': os.getenv('CLICKHOUSE_USERNAME'),
    'password': os.getenv('CLICKHOUSE_PASSWORD'),
    'database': os.getenv('CLICKHOUSE_DATABASE', 'news'),
}

# Native TCP interface configuration (for clickhouse_driver)
CLICKHOUSE_NATIVE_CONFIG = {
    'host': os.getenv('CLICKHOUSE_HOST'),
    'port': int(os.getenv('CLICKHOUSE_NATIVE_PORT', 9000)),  # Native TCP interface
    'user': os.getenv('CLICKHOUSE_USERNAME'),
    'password': os.getenv('CLICKHOUSE_PASSWORD'),
    'database': os.getenv('CLICKHOUSE_DATABASE', 'news'),
}

# Remove None values from configs
CLICKHOUSE_CONFIG = {k: v for k, v in CLICKHOUSE_CONFIG.items() if v is not None}
CLICKHOUSE_NATIVE_CONFIG = {k: v for k, v in CLICKHOUSE_NATIVE_CONFIG.items() if v is not None}

print("ClickHouse HTTP configuration:", {k: '***' if k == 'password' else v for k, v in CLICKHOUSE_CONFIG.items()})
print("ClickHouse Native configuration:", {k: '***' if k == 'password' else v for k, v in CLICKHOUSE_NATIVE_CONFIG.items()})

# Exchange configurations
OKX_CONFIG = {
    'api_key': os.getenv('OKX_API_KEY'),
    'api_secret': os.getenv('OKX_API_SECRET'),
    'password': os.getenv('OKX_PASSWORD'),
}

# Remove None values from config
OKX_CONFIG = {k: v for k, v in OKX_CONFIG.items() if v is not None}
print("OKX configuration:", {k: '***' if k in ['api_secret', 'password'] else v for k, v in OKX_CONFIG.items()}) 