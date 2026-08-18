import threading
import uuid
from datetime import datetime
from typing import Dict, List, Any

import httpx
import os


class EnvironmentRegistry:
    def __init__(self):
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._logs: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def register_agent(self, name: str, url: str, purpose: str) -> Dict[str, Any]:
        with self._lock:
            agent_id = str(uuid.uuid4())
            agent = {
                "id": agent_id,
                "name": name,
                "url": url,
                "purpose": purpose,
                "created_at": datetime.utcnow().isoformat(),
            }
            self._agents[agent_id] = agent
            return agent

    def list_agents(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._agents.values())

    def get_agent(self, agent_id: str) -> Dict[str, Any] | None:
        with self._lock:
            return self._agents.get(agent_id)

    def log(self, entry: Dict[str, Any]):
        with self._lock:
            entry["timestamp"] = datetime.utcnow().isoformat()
            self._logs.insert(0, entry)

    def get_logs(self, agent_id: str | None = None) -> List[Dict[str, Any]]:
        with self._lock:
            if agent_id:
                return [l for l in self._logs if l.get("agent_id") == agent_id]
            return list(self._logs)

    def trigger(self, agent_id: str, message: str) -> Dict[str, Any]:
        agent = self.get_agent(agent_id)
        if not agent:
            raise KeyError("agent not found")

        payload = {"message": message, "purpose": agent.get("purpose")}

        try:
            resp = httpx.post(agent["url"], json=payload, timeout=10.0)
            try:
                content = resp.json()
            except Exception:
                content = resp.text

            entry = {
                "agent_id": agent_id,
                "agent_name": agent.get("name"),
                "request": payload,
                "response": content,
                "status_code": resp.status_code,
            }
            self.log(entry)
            return entry

        except Exception as error:
            entry = {
                "agent_id": agent_id,
                "agent_name": agent.get("name"),
                "request": payload,
                "response": str(error),
                "status_code": None,
            }
            self.log(entry)
            raise


registry = EnvironmentRegistry()
