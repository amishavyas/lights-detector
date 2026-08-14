from alerts import monitor_aurora

if __name__ == "__main__":
    # Runs forever — Render's Background Worker keeps this process
    # alive and restarts it automatically if it ever crashes.
    monitor_aurora()
