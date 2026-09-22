#!/usr/bin/env python3
from influxdb_client import InfluxDBClient

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "MEYJSGt1deHSpykljWgrRCTVG9H5Jj9hJWum5Mo8NxFgY_OjwqJAWL0lV2f2jURrr-FfS-FoIIMTohqP2vVJKg=="

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN)
orgs_api = client.organizations_api()
orgs = orgs_api.find_organizations()

print("Available organizations:")
for org in orgs:
    print(f"  - Name: {org.name}")
    print(f"    ID: {org.id}")

client.close()