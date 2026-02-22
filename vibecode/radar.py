from pathlib import Path
from datetime import datetime

targets = Path("radar/targets.txt")

log = Path("logs/RADAR_LOG.md")
log.parent.mkdir(exist_ok=True)

now = datetime.utcnow().isoformat()

if targets.exists():
    with open(targets) as f:
        data = f.read()
else:
    data = "No targets found"

with open(log,"a") as f:
    f.write(f"\n## Radar Scan {now}\n")
    f.write(data+"\n")
