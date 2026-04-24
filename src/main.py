from __future__ import annotations

import argparse
import json
import sys

from src.app_service import AgentService


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Run the Lab 17 multi-memory agent.")
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--query")
    parser.add_argument("--mode", choices=["baseline", "memory"], default="memory")
    args = parser.parse_args()

    service = AgentService()
    if args.query:
        result = service.run_agent_turn(args.user_id, args.session_id, args.query, args.mode)
        print(result["response"])
        print(json.dumps({"route_decision": result["route_decision"], "metrics": result["metrics"]}, ensure_ascii=False, indent=2))
        return

    print("Interactive mode. Type 'exit' to stop.")
    while True:
        query = input("You> ").strip()
        if query.lower() in {"exit", "quit"}:
            break
        result = service.run_agent_turn(args.user_id, args.session_id, query, args.mode)
        print(f"Agent> {result['response']}")
        print(json.dumps(result["route_decision"], ensure_ascii=False))


if __name__ == "__main__":
    main()
