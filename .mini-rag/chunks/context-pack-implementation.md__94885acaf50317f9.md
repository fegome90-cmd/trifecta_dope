# Validar segment existe
    builder = ContextPackBuilder(args.segment, args.repo_root)
    if not builder.segment_path.exists():
        raise ValueError(f"Segment path does not exist: {builder.segment_path}")
