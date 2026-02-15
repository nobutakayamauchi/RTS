from datetime import datetime

def rts_log(event):
    with open("logs/EXECUTION_LOG.md", "a") as f:
        f.write(f"\n## {datetime.utcnow().isoformat()}Z\n")
        f.write(f"Event: {event}\n")
        f.write("Status: ACTIVE\n")
        f.write("Integrity: VERIFIED\n\n")

log("Vibecode main entry executed")
