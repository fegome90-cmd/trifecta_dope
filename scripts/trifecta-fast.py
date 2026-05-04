#!/usr/bin/env python3
"""
Official fast-path proxy to the Trifecta F1 Daemon Unix Socket.
Designed for automated agents requiring sub-50ms latencies.
Uses standard library + minimal pure domain modules to avoid initialization overhead.
"""

import sys
import json
import argparse
from pathlib import Path

# Add project root to path so we can import src.domain and src.infrastructure.daemon_client
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from src.infrastructure.daemon_client import get_socket_path, call_daemon

def parse_args():
    parser = argparse.ArgumentParser(description="Fast proxy to Trifecta Daemon")
    parser.add_argument("command", choices=["search", "get", "oracle"], help="Command to execute")
    parser.add_argument("--query", "-q", help="Search query")
    parser.add_argument("--ids", "-i", help="Comma-separated IDs for get")
    parser.add_argument("--limit", "-l", type=int, default=5, help="Max results for search/oracle")
    parser.add_argument("--mode", "-m", default="excerpt", help="Mode for get")
    parser.add_argument("--segment", "-s", default=".", help="Segment path")
    parser.add_argument("--enable-lint", action="store_true", help="Enable query linting")
    parser.add_argument("--budget-token-est", type=int, default=1500, help="Max tokens for get")
    return parser.parse_args()

def main():
    args = parse_args()
    segment_path = Path(args.segment).resolve()
    socket_path = get_socket_path(segment_path)
    
    if not socket_path.exists():
        print(f"Error: Daemon socket not found at {socket_path}. Is the daemon running for {segment_path}?", file=sys.stderr)
        sys.exit(1)
        
    tool_name = f"ctx_{args.command}"
    tool_args = {}
    
    if args.command == "search":
        if not args.query:
            print("Error: --query is required for search", file=sys.stderr)
            sys.exit(1)
        tool_args = {
            "query": args.query,
            "k": args.limit,
            "enable_lint": args.enable_lint
        }
    elif args.command == "get":
        if not args.ids:
            print("Error: --ids is required for get", file=sys.stderr)
            sys.exit(1)
        tool_args = {
            "ids": [i.strip() for i in args.ids.split(",")],
            "mode": args.mode,
            "budget_token_est": args.budget_token_est
        }
    elif args.command == "oracle":
        if not args.query:
            print("Error: --query is required for oracle", file=sys.stderr)
            sys.exit(1)
        tool_args = {
            "query": args.query,
            "k": args.limit
        }
        
    res = call_daemon(socket_path, tool_name, tool_args)
    
    if res.is_err():
        print(f"Daemon Error: {res.error}", file=sys.stderr)
        sys.exit(1)
        
    output = res.unwrap()
    if isinstance(output, dict) or isinstance(output, list):
        print(json.dumps(output, indent=2))
    else:
        print(output)

if __name__ == "__main__":
    main()
