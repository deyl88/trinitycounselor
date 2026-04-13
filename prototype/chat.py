"""
Trinity Quick Start — interactive terminal chat.

This lets you talk to any of the three Trinity agents directly from your terminal.
No databases, no Docker, no setup beyond your API key.

Usage:
    python chat.py
"""

import os
import sys
import json
import urllib.request
import urllib.error
import subprocess
import threading
import time


def start_server():
    """Start the FastAPI server in the background."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8765", "--log-level", "error"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    time.sleep(2)  # Give the server a moment to start
    return proc


def post(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def create_relationship(server, partner_a, partner_b):
    return post(f"{server}/relationships", {
        "partner_a_name": partner_a,
        "partner_b_name": partner_b,
    })


def solo_chat(server, rel_id, partner, message):
    return post(f"{server}/solo", {
        "relationship_id": rel_id,
        "partner": partner,
        "message": message,
    })


def joint_chat(server, rel_id, partner_a_msg, partner_b_msg):
    return post(f"{server}/joint", {
        "relationship_id": rel_id,
        "partner_a_message": partner_a_msg,
        "partner_b_message": partner_b_msg,
    })


def sync(server, rel_id):
    post(f"{server}/sync", {"relationship_id": rel_id})


def banner(text, char="─"):
    width = 60
    print(f"\n{char * width}")
    print(f"  {text}")
    print(f"{char * width}")


def chat_loop(server, rel_id, partner_name, partner_key):
    banner(f"🔒 {partner_name}'s Private Session  (type 'quit' to go back)")
    print(f"  Everything here is private to {partner_name}.")
    print(f"  Your partner cannot see this.\n")

    while True:
        try:
            msg = input(f"  {partner_name}: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if msg.lower() in ("quit", "exit", "q", "back"):
            break
        if not msg:
            continue

        print(f"\n  [thinking...]\n")
        try:
            result = solo_chat(server, rel_id, partner_key, msg)
            response = result.get("response", result.get("message", ""))
            print(f"  Counselor: {response}\n")
        except Exception as e:
            print(f"  [error: {e}]\n")


def joint_loop(server, rel_id, partner_a_name, partner_b_name):
    banner("💬 Joint Session  (type 'quit' to go back)")
    print(f"  Both {partner_a_name} and {partner_b_name} are present.")
    print(f"  The Relationship Counselor mediates. Private history is not shared.\n")

    while True:
        print(f"  Who is speaking?")
        print(f"  [1] {partner_a_name}")
        print(f"  [2] {partner_b_name}")
        print(f"  [q] Back to menu")
        choice = input("  → ").strip()

        if choice in ("q", "quit"):
            break
        elif choice == "1":
            speaker = partner_a_name
            is_a = True
        elif choice == "2":
            speaker = partner_b_name
            is_a = False
        else:
            continue

        try:
            msg = input(f"\n  {speaker}: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not msg:
            continue

        print(f"\n  [thinking...]\n")
        try:
            if is_a:
                result = joint_chat(server, rel_id, msg, "")
            else:
                result = joint_chat(server, rel_id, "", msg)
            response = result.get("response", "")
            print(f"  Relationship Counselor: {response}\n")
        except Exception as e:
            print(f"  [error: {e}]\n")


def main():
    # Check for API key
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                if line.startswith("ANTHROPIC_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    if key and key != "your_key_here":
                        os.environ["ANTHROPIC_API_KEY"] = key

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n  ⚠️  No API key found.")
        print("  Add your Anthropic API key to prototype/.env:")
        print("  ANTHROPIC_API_KEY=sk-ant-...\n")
        sys.exit(1)

    print("\n  Starting Trinity...", end="", flush=True)
    server_proc = start_server()
    server = "http://localhost:8765"
    print(" ready.\n")

    try:
        # Get partner names
        banner("Welcome to Trinity", "═")
        print("  Trinity is a private counseling space for couples.")
        print("  Each partner has their own private AI counselor.")
        print("  The Relationship Counselor mediates joint sessions.\n")

        partner_a = input("  Partner A's first name: ").strip() or "Alex"
        partner_b = input("  Partner B's first name: ").strip() or "Jordan"

        # Create relationship
        try:
            result = create_relationship(server, partner_a, partner_b)
            rel_id = result["relationship_id"]
        except Exception:
            # Fallback if endpoint format differs
            rel_id = "demo-session"

        # Main menu
        while True:
            banner(f"Trinity — {partner_a} & {partner_b}")
            print(f"  [1] {partner_a}'s private session  (Agent A)")
            print(f"  [2] {partner_b}'s private session  (Agent B)")
            print(f"  [3] Joint session  (Relationship Counselor)")
            print(f"  [4] Sync insights to relational model")
            print(f"  [q] Quit")
            print()

            choice = input("  → ").strip()

            if choice == "1":
                chat_loop(server, rel_id, partner_a, "A")
            elif choice == "2":
                chat_loop(server, rel_id, partner_b, "B")
            elif choice == "3":
                # Sync before joint session for best context
                try:
                    sync(server, rel_id)
                except Exception:
                    pass
                joint_loop(server, rel_id, partner_a, partner_b)
            elif choice == "4":
                print("\n  Syncing insights...", end="", flush=True)
                try:
                    sync(server, rel_id)
                    print(" done.\n")
                except Exception as e:
                    print(f" failed ({e})\n")
            elif choice in ("q", "quit"):
                break

    finally:
        server_proc.terminate()
        print("\n  Trinity closed. Take care.\n")


if __name__ == "__main__":
    main()
