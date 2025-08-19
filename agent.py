# agent.py
import os
import dotenv

dotenv.load_dotenv()

from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from prompts import SYSTEM_PROMPT
from tools import tools  # unified tools import

# ---- LLM ----
llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
)

# ---- Agent ----
agent = create_react_agent(llm, tools)

# ---- Graph State & Node ----
class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=f"You are the Book Nook literary guide. {SYSTEM_PROMPT}")] + messages
    result = agent.invoke({"messages": messages})
    new_messages = result["messages"][len(messages):]
    return {"messages": new_messages}

# ---- Build Graph ----
builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)
graph = builder.compile()

# ---- CLI loop (optional) ----
def stream_graph_updates(user_input: str):
    user_message = HumanMessage(content=user_input)
    for event in graph.stream({"messages": [user_message]}):
        for value in event.values():
            if value and "messages" in value and value["messages"]:
                for msg in value["messages"]:
                    if isinstance(msg, AIMessage) and msg.content and not getattr(msg, "tool_calls", None):
                        print("Assistant:", msg.content)

if __name__ == "__main__":
    print("Assistant: Hello! Welcome to the Book Nook. How can I help you today?")
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "bye"]:
                print("Happy reading! Goodbye!")
                break
            stream_graph_updates(user_input)
        except Exception as e:
            print(f"An error occurred: {e}")
            print("\nDefaulting to a sample question…")
            stream_graph_updates("What are your store hours?")
