int(total_events * session_ratio)

    events = []
    base_time = datetime.now()

    for i in range(ctx_count):
        events.append(generate_event(random.choice(["ctx.search", "ctx.get", "ctx.sync"]),
                                      base_time + timedelta(seconds=i)))

    for i in range(lsp_count):
        events.append(generate_event(random.choice(["lsp.spawn", "lsp.request"]),
                                      base_time + timedelta(seconds=ctx_count+i)))

    for i in range(session_count):
        events.append(generate_event("session.entry",
                                      base_time + timedelta(seconds=ctx_count+lsp_count+i)))

    # Shuffle to mimic real interleaved events
    random.shuffle(events)

    with open(output, "w") as f:
        for event in events:
            f.write(json.dumps(event)+ "\n")

    print(f"✅ Generated {len(events)} events to {output}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=int, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ctx-ratio", type=float, default=0.7)
    parser.add_argument("--lsp-ratio", type=float, default=0.2)
    parser.add_argument("--session-ratio", type=float, default=0.1)
    args = parser.parse_args()

    generate_dataset(args.events, args.ctx_ratio, args.lsp_ratio, args.
