#!/usr/bin/env python3
# RTS PRO Starter Kit - Guided Setup (no deps)
import os, subprocess, sys, datetime, textwrap, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))

def run(cmd):
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)

def have(cmd):
    return shutil.which(cmd) is not None

def header(title):
    print("\n" + "="*60)
    print(title)
    print("="*60)

def write_install_log(msg):
    os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
    p = os.path.join(ROOT, "logs", "INSTALL_LOG.md")
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(p, "a", encoding="utf-8") as f:
        f.write(f"- {ts}  {msg}\n")

def main():
    header("RTS PRO Starter Kit - Guided Setup")
    print("This will set up RTS locally (and optionally Git).")
    print("Nothing is uploaded anywhere unless YOU push it to GitHub.\n")

    py_ok = sys.version_info >= (3, 9)
    print(f"Python: {sys.version.split()[0]}  -> {'OK' if py_ok else 'Too old'}")
    if not py_ok:
        print("\nPlease install a newer Python 3 (3.9+). Then run START_HERE.command again.")
        sys.exit(1)

    git_available = have("git")
    print(f"Git: {'found' if git_available else 'NOT found'}")

    # 1) sanity check folders
    for d in ["logs", "evolution", "vibecode"]:
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)

    # 2) initialize git repo (optional but recommended)
    if git_available:
        git_dir = os.path.join(ROOT, ".git")
        if os.path.exists(git_dir):
            print("\nGit repo already initialized.")
        else:
            ans = input("\nInitialize a local Git repo here? (recommended) [Y/n]: ").strip().lower()
            if ans in ("", "y", "yes"):
                r = run(["git", "init"])
                if r.returncode != 0:
                    print("\nGit init failed:\n", r.stderr)
                else:
                    # add + commit
                    run(["git", "add", "-A"])
                    run(["git", "commit", "-m", "RTS: baseline (PRO starter kit)"])
                    print("Git initialized + baseline commit created.")
    else:
        print("\nTip: If you want Git history + rollback, install Git, then run again.")

    # 3) write install marker
    write_install_log("RTS PRO setup completed")

    header("Next steps (beginner-friendly)")
    print(textwrap.dedent("""    1) If you're using Claude Code / agent tools:
       - Put your working files inside this folder.
       - Keep ALL changes committed (Git) so you can roll back.

    2) If you want GitHub backup (optional):
       - Install GitHub Desktop (Mac).
       - 'Add Existing Repository' -> choose this folder -> Publish to GitHub.

    3) If something breaks:
       - (Git users) run:  git log  /  git reset --hard <commit>
       - Or simply re-download the kit and compare files.

    If you're stuck, take a screenshot and send it.
    """).strip())

if __name__ == "__main__":
    main()
