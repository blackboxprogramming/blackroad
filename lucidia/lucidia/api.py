from fastapi import FastAPI
from pydantic import BaseModel
from .agent import chat

app = FastAPI(title="Lucidia (PoC)")

class ChatReq(BaseModel):
    prompt: str

@app.post("/chat")
def chat_endpoint(req: ChatReq):
    resp = chat(req.prompt)
    return {"response": resp}

class SuggestReq(BaseModel):
    prompt: str

@app.post("/suggest_action")
def suggest_action(req: SuggestReq):
    suggestion = "echo 'This is a suggested command based on: {}'".format(req.prompt)
    return {"suggestion": suggestion, "auto_execute": False}

class ApproveReq(BaseModel):
    command: str

@app.post("/approve_action")
def approve_action(req: ApproveReq):
    # Safety: DO NOT auto-execute without explicit admin tooling.
    return {"status": "approved_recorded", "command": req.command, "note": "Execution must be performed manually by operator."}
