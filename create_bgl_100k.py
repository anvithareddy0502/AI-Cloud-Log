import csv

raw_file = "data/BGL/BGL_full.log"
structured_file = "data/BGL/BGL_full.log_structured.csv"
output_file = "data/BGL/opensearch_bgl_100k_timestamped.csv"

LIMIT = 100000

with open(raw_file, "r", encoding="utf-8", errors="ignore") as raw, \
     open(structured_file, "r", encoding="utf-8", newline="") as structured, \
     open(output_file, "w", encoding="utf-8", newline="") as out:

    reader = csv.DictReader(structured)

    writer = csv.writer(out)
    writer.writerow([
        "timestamp",
        "line_id",
        "content",
        "event_id",
        "event_template"
    ])

    count = 0

    for raw_line, row in zip(raw, reader):

        if count >= LIMIT:
            break

        parts = raw_line.strip().split()

        # BGL timestamp is the 5th token
        if len(parts) < 5:
            continue

        timestamp = parts[4]

        writer.writerow([
            timestamp,
            row["LineId"],
            row["Content"],
            row["EventId"],
            row["EventTemplate"]
        ])

        count += 1

print(f"Created {count} rows")
print(f"Output: {output_file}")