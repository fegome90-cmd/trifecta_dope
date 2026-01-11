es", []),
                "commands": event["args"].get("commands", []),
                "outcome": event["result"]["outcome"],
                "tags": event["x"].get("tags", [])
            }
        else:  # raw
            entry = event

        entries.append(entry)

    # Apply --last limit
    if last:
        entries = entries[-last:]

    print(json.dumps(entries, indent=2))
```
