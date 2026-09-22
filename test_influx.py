# filepath: ~/smartroom/test_influx.py
#!/usr/bin/env python3
"""Test InfluxDB Connection"""

try:
    from influxdb_client import InfluxDBClient
    
    INFLUX_URL = "http://localhost:8086"
    INFLUX_TOKEN = "MEYJSGt1deHSpykljWgrRCTVG9H5Jj9hJWum5Mo8NxFgY_OjwqJAWL0lV2f2jURrr-FfS-FoIIMTohqP2vVJKg=="
    INFLUX_ORG = "smartroom"
    
    print("Testing InfluxDB connection...")
    
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    
    # Test ping
    health = client.ping()
    print(f"? InfluxDB ping successful: {health}")
    
    # Test buckets list
    buckets_api = client.buckets_api()
    buckets = buckets_api.find_buckets()
    print(f"? Available buckets:")
    for bucket in buckets.buckets:
        print(f"  - {bucket.name} (id: {bucket.id})")
    
    # Check if 'sensor_data' bucket exists
    sensor_bucket = None
    for bucket in buckets.buckets:
        if bucket.name == "sensor_data":
            sensor_bucket = bucket
            break
    
    if sensor_bucket:
        print(f"? sensor_data bucket found: {sensor_bucket.id}")
    else:
        print("? sensor_data bucket not found, creating it...")
        from influxdb_client.domain.bucket import Bucket
        new_bucket = Bucket(name="sensor_data", org_id=INFLUX_ORG)
        created = buckets_api.create_bucket(bucket=new_bucket)
        print(f"? Created sensor_data bucket: {created.id}")
    
    client.close()
    print("\n?? InfluxDB connection test successful!")
    print("? Token valid")
    print("? Organization accessible")
    print("? Bucket ready")
    
except ImportError:
    print("? influxdb-client not installed!")
    print("Run: pip install influxdb-client")
except Exception as e:
    print(f"? InfluxDB connection failed: {e}")