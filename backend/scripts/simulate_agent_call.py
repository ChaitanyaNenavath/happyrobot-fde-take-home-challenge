import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.agent import handle_agent_turn, start_agent_session


def main():

    session = start_agent_session()
    print(f"Agent: {session['response']}")

    turns = [
        "My MC is 123456",
        "Dallas to Atlanta dry van",
        "I can do it for 1850",
    ]

    for utterance in turns:
        print(f"Carrier: {utterance}")
        response = handle_agent_turn(session["session_id"], utterance)
        print(f"Agent: {response['response']}")


if __name__ == "__main__":
    main()
