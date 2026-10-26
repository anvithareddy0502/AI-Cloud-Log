import csv
import json
import urllib.request

CSV_FILE = "data/BGL/opensearch_bgl_100k_timestamped.csv"
URL = "http://localhost:9200/bgl_logs_ts/_bulk"

batch = []
total = 0
batch_size = 1000

with open(CSV_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        batch.append(
            json.dumps({"index": {}})
        )

        batch.append(
            json.dumps({
                "timestamp": row["timestamp"],
                "line_id": row["line_id"],
                "content": row["content"],
                "event_id": row["event_id"],
                "event_template": row["event_template"]
            })
        )

        if len(batch) >= batch_size * 2:
            data = ("\n".join(batch) + "\n").encode("utf-8")

            req = urllib.request.Request(
                URL,
                data=data,
                headers={"Content-Type": "application/x-ndjson"},
                method="POST"
            )

            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read())

            if result.get("errors"):
                print("ERROR in batch")
                print(result)

            total += batch_size
            print(f"Loaded approximately {total} records")

            batch = []

    if batch:
        data = ("\n".join(batch) + "\n").encode("utf-8")

        req = urllib.request.Request(
            URL,
            data=data,
            headers={"Content-Type": "application/x-ndjson"},
            method="POST"
        )

        urllib.request.urlopen(req)

print(f"Finished loading {total + len(batch)//2} records")