import os
import glob

ISSUE = os.environ.get("ISSUE_NUMBER")

INCIDENT_DIR = "incidents"


def close_incident():

    if not ISSUE:
        print("No issue number")
        return

    files = glob.glob(f"{INCIDENT_DIR}/*.md")

    for f in files:

        with open(f,"r",encoding="utf-8") as file:
            content = file.read()

        if f"source_issue: #{ISSUE}" not in content:
            continue

        if "status: Closed" in content:
            print("already closed")
            continue

        content = content.replace(
            "status: Open",
            "status: Closed"
        )

        with open(f,"w",encoding="utf-8") as file:
            file.write(content)

        print("Closed:",f)


if __name__ == "__main__":
    close_incident()
