from __future__ import annotations

from pathlib import Path
from typing import Iterable

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FileSearchTool, PromptAgentDefinition
from azure.identity import DefaultAzureCredential


AGENT_INSTRUCTIONS = """
You are Northstar Operations Intelligence Agent, a retrieval-grounded assistant.

Rules:
1. Use the file-search knowledge base for factual questions about Northstar reports, policies, or SOPs.
2. Answer only from retrieved evidence. If the documents do not establish a fact, say that it is unknown or not confirmed.
3. Never invent a root cause, incident, threshold, number, or policy requirement.
4. Clearly distinguish reported facts from analysis or recommendations.
5. When a policy threshold applies, state both the observed value and the threshold.
6. Keep answers concise and decision-oriented.
7. End answers with a short 'Sources' section naming the document(s) used when the document names are available in context.
""".strip()


class FoundryRAGClient:
    """Small wrapper around Microsoft Foundry project, agent, and response APIs."""

    def __init__(self, project_endpoint: str, model_deployment_name: str):
        self.project_endpoint = project_endpoint
        self.model_deployment_name = model_deployment_name
        self.credential = DefaultAzureCredential()
        self.project = AIProjectClient(
            endpoint=self.project_endpoint,
            credential=self.credential,
        )
        self.openai = self.project.get_openai_client()

    def create_vector_store(
        self,
        files: Iterable[Path],
        name: str = "northstar-operations-kb",
    ) -> str:
        vector_store = self.openai.vector_stores.create(name=name)

        for file_path in files:
            with file_path.open("rb") as file_handle:
                self.openai.vector_stores.files.upload_and_poll(
                    vector_store_id=vector_store.id,
                    file=file_handle,
                )

        return vector_store.id

    def create_agent(
        self,
        vector_store_id: str,
        agent_name: str = "northstar-operations-rag",
    ):
        return self.project.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=self.model_deployment_name,
                instructions=AGENT_INSTRUCTIONS,
                tools=[FileSearchTool(vector_store_ids=[vector_store_id])],
            ),
            description=(
                "Retrieval-grounded operations intelligence agent using "
                "Microsoft Foundry file search."
            ),
        )

    def create_conversation(self) -> str:
        conversation = self.openai.conversations.create()
        return conversation.id

    def ask(
        self,
        agent_name: str,
        question: str,
        conversation_id: str | None = None,
    ) -> tuple[str, str]:
        if not conversation_id:
            conversation_id = self.create_conversation()

        response = self.openai.responses.create(
            conversation=conversation_id,
            input=question,
            extra_body={
                "agent_reference": {
                    "name": agent_name,
                    "type": "agent_reference",
                }
            },
        )

        return response.output_text, conversation_id

    def delete_agent_version(self, agent_name: str, agent_version: str) -> None:
        self.project.agents.delete_version(
            agent_name=agent_name,
            agent_version=agent_version,
        )

    def delete_vector_store(self, vector_store_id: str) -> None:
        self.openai.vector_stores.delete(vector_store_id)
