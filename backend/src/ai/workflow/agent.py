import os
from typing import Literal

from ai.workflow.prompts import agent_prompt
from ai.workflow.tools import TOOLS
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.config import get_stream_writer
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt.tool_node import ToolNode


class AgentState(MessagesState):
    thread_title: str
    summary: str


# TODO: 1. Add long-term memory (user profile, contextual/episodic memory)
# TODO: 2. Add modification workflow for recipes
# TODO: 3. Future optimization - Background summarization?
# TODO: 4. Add a way to update the thread title in the background, maybe a sub-workflow?
# TODO: 5. Should we parallelize the thread title update and AI response?


class AgentFactory:
    def __init__(
        self,
        user_id: str,
        thread_id: str,
        checkpointer: BaseCheckpointSaver,
    ):
        self.user_id = user_id
        self.thread_id = thread_id
        self.checkpointer = checkpointer
        self.agent_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,
            api_key=os.getenv("GOOGLE_API_KEY"),
        )

    def build(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("call_model", self.call_model)
        workflow.add_node("tools", ToolNode(tools=TOOLS))
        workflow.add_node("update_thread_title", self.update_thread_title)
        workflow.add_node("summarize_conversation", self.summarize_conversation)

        workflow.set_entry_point("call_model")
        workflow.add_conditional_edges("call_model", self.route_model_response)
        workflow.add_edge("tools", "call_model")
        workflow.add_edge("summarize_conversation", "__end__")
        workflow.add_edge("update_thread_title", "__end__")

        return workflow.compile(name="food_agent", checkpointer=self.checkpointer)

    async def update_thread_title(self, state: AgentState):
        messages = state.get("messages", [])
        summary = state.get("summary", "")

        thread_title_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.1,
            api_key=os.getenv("GOOGLE_API_KEY"),
        )

        title_message = (
            "Review the recent conversation messages above and return ONLY a concise thread title (max 60 characters).\n\n"
            "Identify the main topic, concern, or request from the user's messages.\n\n"
            "Focus on: What are they asking for? What's their situation? What kind of support do they need?\n\n"
            "Use warm, conversational language that feels natural and supportive.\n\n"
            "Examples: 'Need dinner ideas', 'Feeling stressed about cooking', 'Want to try new recipes', 'Help with meal planning'\n\n"
            "IMPORTANT: Return ONLY the title text. No markdown, no explanations, no quotes."
        )

        recent_messages = messages[-5:] + [HumanMessage(content=title_message)]
        response = await thread_title_llm.ainvoke(recent_messages)
        response_content = str(response.content).strip()

        write = get_stream_writer()
        write({"event": "thread_title_updated", "thread_title": response_content})

        return {"thread_title": response_content}

    async def summarize_conversation(self, state: AgentState):
        messages = state.get("messages", [])

        summary_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.1,  # Lower temperature for more consistent summaries
            api_key=os.getenv("GOOGLE_API_KEY"),
        )

        summary = state.get("summary", "")
        if summary:
            summary_message = (
                f"Previous summary: {summary}\n\n"
                "Based on the conversation above, extend the previous summary to include the new context. "
                "Keep it concise (2-3 sentences total) and focus on the user's main concerns, preferences, or requests. "
                "Be brief and factual."
            )
        else:
            summary_message = (
                "Provide a concise 1-2 sentence summary of the conversation above. "
                "Focus on the user's main concerns, preferences, or requests. Be brief and factual."
            )

        recent_messages = messages[-8:] + [HumanMessage(content=summary_message)]
        response = await summary_llm.ainvoke(recent_messages)
        response_content = str(response.content).strip()

        write = get_stream_writer()
        write({"event": "summary_updated", "summary": response_content})

        delete_messages = [RemoveMessage(id=str(m.id)) for m in messages[:-8]]

        return {"summary": response_content, "messages": delete_messages}

    async def call_model(self, state: AgentState) -> AgentState:
        prompt_template = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(agent_prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        chain = prompt_template | self.agent_llm.bind_tools(TOOLS)
        response = await chain.ainvoke(
            {
                "messages": state.get("messages", []),
            }
        )

        if isinstance(response, AIMessage) and response.tool_calls:
            write = get_stream_writer()
            name = response.tool_calls[0]["name"]
            args = response.tool_calls[0]["args"]
            if name == "create_recipe":
                write({"event": "recipe_generation_started", "tool_name": name, "tool_input": args})

        return {"messages": [response]}  # type: ignore

    def route_model_response(
        self, state: AgentState
    ) -> Literal["tools", "summarize_conversation", "update_thread_title", "__end__"]:
        messages = state.get("messages", [])
        last_message = messages[-1]
        if not isinstance(last_message, AIMessage):
            raise ValueError("Expected an AI message, got: ", {type(last_message).__name__})

        if len(last_message.tool_calls) > 0:
            return "tools"
        # TODO: We should do these as background tasks
        elif len(messages) > 5 and state.get("thread_title", None) is None:
            return "update_thread_title"
        elif len(messages) > 8:
            return "summarize_conversation"
        else:
            return "__end__"
