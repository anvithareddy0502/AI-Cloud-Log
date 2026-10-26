import csv

RAW = "data/BGL/BGL_full.log"
STRUCTURED = "data/BGL/BGL_full.log_structured.csv"
OUT = "data/BGL/BGL_JUNE12_COMMON.csv"

START = "2005-06-12-00:00:00"
END = "2005-06-13-00:00:00"

count = 0

with open(RAW, encoding="utf-8", errors="ignore") as rf, \
     open(STRUCTURED, encoding="utf-8", newline="") as sf, \
     open(OUT, "w", encoding="utf-8", newline="") as of:

    reader = csv.DictReader(sf)

    writer = csv.writer(of)
    writer.writerow([
        "timestamp",
        "line_id",
        "content",
        "event_id",
        "event_template",
        "ground_truth"
    ])

    for raw, row in zip(rf, reader):

        p = raw.strip().split()

        if len(p) < 5:
            continue

        timestamp = p[4]

        # BGL timestamp: 2005-06-03-15.42.50.363779
        date = timestamp[:10]
        time = timestamp[11:19].replace(".", ":")

        iso = f"{date}-{time}"

        if START <= iso < END:

            # BGL: "-" = normal, anything else = anomaly
            label = 0 if p[0] == "-" else 1

            writer.writerow([
                timestamp,
                row["LineId"],
                row["Content"],
                row["EventId"],
                row["EventTemplate"],
                label
            ])

            count += 1

print("Created:", OUT)
print("Rows:", count)