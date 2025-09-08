import os
from datetime import datetime
from pprint import pprint
import uvicorn, json
from uuid import uuid4
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
import schemas

from a2a.types import AgentCard, AgentCapabilities, AgentSkill, AgentProvider
import a2a.types as a2a_types


load_dotenv()

TELEX_API_KEY = os.getenv("TELEX_API_KEY")
TELEX_API_URL = os.getenv("TELEX_API_URL")

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def read_root():
    return '<p style="font-size:30px">SEO agent</p>'


@app.get("/.well-known/agent.json")
def get_agent_card(request: Request):
    external_base = request.headers.get("x-external-base-url", "")
    current_base_url = str(request.base_url).rstrip("/") + external_base

    capabilities = AgentCapabilities(pushNotifications=True)

    skills = AgentSkill(
        id="all-caps",
        name="Capitalize all letters",
        description="Capitalize all letters provided",
        inputModes=["text"],
        outputModes=["text"],
        tags=["capitalize"],
    )

    provider = AgentProvider(organization="Telex", url="https://telex.im")

    agent_card = AgentCard(
        name="Capitalizer",
        description="Capitalizes stuff",
        url=current_base_url,
        version="1.0.1",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        capabilities=capabilities,
        skills=[skills],
        provider=provider,
        documentationUrl=f"{current_base_url}/docs",
    )

    card = AgentCard.model_dump(agent_card)

    return card


async def handle_task(
    message: schemas.CapitalizerConfig, task_id: str, context_id: str
):

    message_text = message.target_text.value
    capitalized = message_text.upper()
    print(f"after capitalizing {capitalized}")

    parts = a2a_types.TextPart(text=capitalized)

    message = a2a_types.Message(
        messageId=uuid4().hex, role=a2a_types.Role.agent, parts=[parts]
    )

    artifacts = a2a_types.Artifact(artifactId=uuid4().hex, parts=[parts])

    task = a2a_types.Task(
        id=task_id,
        contextId=context_id,
        status=a2a_types.TaskStatus(
            state=a2a_types.TaskState.completed,
            message=a2a_types.Message(
                messageId=uuid4().hex,
                role=a2a_types.Role.agent,
                parts=[a2a_types.TextPart(text="Success!")],
            ),
        ),
        artifacts=[artifacts],
    )

    print("TASK END: ", datetime.now())

    return task


@app.post("/")
async def handle_request(request: a2a_types.SendMessageRequest):
    try:
        
        message_parts = request.params.message.parts
        target_obj = {}

        for part in message_parts:
            if isinstance(part, a2a_types.DataPart):
                target_obj = part.data


        telex_object_schema = schemas.CapitalizerConfig.model_validate(target_obj)

        context_id = uuid4().hex
        new_task_id = uuid4().hex

        print("TASK START: ", datetime.now())
        result = await handle_task(
            message=telex_object_schema.target_text.value, task_id=new_task_id, context_id=context_id
        )

        response = a2a_types.JSONRPCResponse(id=uuid4().hex, result=result)

        response = response.model_dump(exclude_none=True)
        pprint(response)
        return response
    except json.JSONDecodeError as e:
        error = a2a_types.JSONParseError(data=str(e))
        response = a2a_types.JSONRPCErrorResponse(error=error)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
