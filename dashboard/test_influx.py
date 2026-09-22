import sys
sys.path.append('.')
from app import _get_influx_client, INFLUX_BUCKET
client, write, query = _get_influx_client()
q = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "energy_monitor")
  |> filter(fn: (r) => r["_field"] == "energy_kwh")
  |> last()
'''
res = query.query(q)
for table in res:
    for rec in table.records:
        print(rec.values.get('device'), rec.get_value())
