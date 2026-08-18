from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI(title="Langraph Demo Agent")


class Payload(BaseModel):
    message: str
    purpose: str | None = None
    instructions: List[str] | None = None


# Define a small allowed instruction set for this demo agent
ALLOWED_INSTRUCTIONS = {"read_faq", "lookup_customer", "send_email"}


@app.post("/respond")
async def respond(payload: Payload):
    # Validate instructions if present
    instructions = payload.instructions or []
    invalid = [ins for ins in instructions if ins not in ALLOWED_INSTRUCTIONS]
    if invalid:
        return {
            "agent": "langraph-demo",
            "status": "blocked",
            "reason": "invalid_instructions",
            "invalid_instructions": invalid,
            "original": payload.message,
            "purpose": payload.purpose,
        }

    # If instructions are allowed, simulate execution results
    results = []
    for ins in instructions:
        if ins == "read_faq":
            results.append({"instruction": ins, "result": f"Found FAQ answer for '{payload.message[:50]}'"})
        elif ins == "lookup_customer":
            results.append({"instruction": ins, "result": {"customer_id": "cust_123", "name": "Demo Customer"}})
        elif ins == "send_email":
            results.append({"instruction": ins, "result": "Email queued"})

    # Fallback: if no instructions, produce a simple graph-like summary
    if not instructions:
        text = payload.message or ""
        words = [w.strip() for w in text.split() if w.strip()]
        nodes = [{"id": f"n{i}", "label": w, "score": len(w)} for i, w in enumerate(words[:8])]
        return {
            "agent": "langraph-demo",
            "status": "completed",
            "original": payload.message,
            "purpose": payload.purpose,
            "summary": f"Processed {len(words)} words",
            "nodes": nodes,
        }

    return {
        "agent": "langraph-demo",
        "status": "completed",
        "original": payload.message,
        "purpose": payload.purpose,
        "results": results,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9001)
