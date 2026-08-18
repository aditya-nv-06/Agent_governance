"""Simple dev test script to exercise the langraph demo agent.

Runs two requests: one with allowed instruction(s) and one with an invalid instruction to show rejection.
"""
import httpx

AGENT_URL = "http://localhost:9001/respond"


def run_test():
    client = httpx.Client(timeout=10.0)

    print("Sending allowed instructions...")
    payload = {"message": "Find FAQs about billing", "instructions": ["read_faq"]}
    r = client.post(AGENT_URL, json=payload)
    print("Status:", r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text)

    print("\nSending mixed (invalid) instructions...")
    payload2 = {"message": "Try disallowed action", "instructions": ["read_faq", "do_harm"]}
    r2 = client.post(AGENT_URL, json=payload2)
    print("Status:", r2.status_code)
    try:
        print(r2.json())
    except Exception:
        print(r2.text)


if __name__ == "__main__":
    run_test()
