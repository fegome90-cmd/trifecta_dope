def main():
    parser = argparse.ArgumentParser(
        description="Generate token-optimized Context Pack from Trifecta documentation",
        epilog="""Examples:
  python ingest_trifecta.py --segment debug_terminal
  python ingest_trifecta.py --segment hemdov --repo-root /path/to/projects
  python ingest_trifecta.py --segment eval --output custom/pack.json --dry-run""",
    )
    parser.add_argument("--segment", "-s", required=True)
    parser.add_argument("--repo-root", "-r", type=Path, default=Path.cwd())
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--dry-run", "-n", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--force", "-f", action="store_true")

    args = parser.parse_args()
