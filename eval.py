# eval.py
import os
import re
import statistics
import dotenv
from typing import Annotated, Dict, List, Tuple
from typing_extensions import TypedDict

dotenv.load_dotenv()

from langsmith import Client, traceable
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from prompts import SYSTEM_PROMPT, CORRECTNESS_PROMPT
from tools import tools  # use unified tools

# ---------- Env + Clients ----------
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
DATASET_ID = os.getenv("DATASET_ID")
if not DATASET_ID:
    raise RuntimeError("❌ DATASET_ID is not set in your .env")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY is not set in your .env")

client = Client(api_key=LANGSMITH_API_KEY)

# ---------- Models ----------
llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GEMINI_API_KEY,
    temperature=0,
)
judge = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GEMINI_API_KEY,
    temperature=0,
)

# ---------- Agent Under Test ----------
class State(TypedDict):
    messages: Annotated[list, add_messages]

def _build_graph():
    agent = create_react_agent(llm, tools)

    def chatbot(state: State):
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=f"You are the Book Nook literary guide. {SYSTEM_PROMPT}")] + messages
        result = agent.invoke({"messages": messages})
        new_messages = result["messages"][len(messages):]
        return {"messages": new_messages}

    builder = StateGraph(State)
    builder.add_node("chatbot", chatbot)
    builder.add_edge(START, "chatbot")
    builder.add_edge("chatbot", END)
    return builder.compile()

graph = _build_graph()

@traceable(name="AOT Stream")
def run_once(user_input: str) -> str:
    user_message = HumanMessage(content=user_input)
    final = ""
    for event in graph.stream({"messages": [user_message]}):
        for value in event.values():
            if value and "messages" in value and value["messages"]:
                for msg in value["messages"]:
                    if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
                        final = msg.content
    return final

@traceable(name="Target Function")
def target_function(inputs: dict) -> dict:
    return {"output": run_once(inputs["HUMAN"])}

# ---------- Evaluators (variety) ----------
def _ask_judge(prompt: str) -> int:
    """Ask Gemini to return a 1–10 integer; clamp and fallback safely."""
    raw = judge.invoke(prompt).content.strip()
    m = re.search(r"(\d{1,2})", raw)
    if not m:
        return 5
    score = int(m.group(1))
    return max(1, min(10, score))

def eval_semantic_similarity(inputs: dict, reference_outputs: dict, outputs: dict):
    q = inputs.get("HUMAN", "")
    ref = reference_outputs.get("AI", "")
    got = outputs.get("output", "")
    prompt = (
        "You are a semantic similarity evaluator. Score 1–10 (10 = same meaning).\n\n"
        f"Question: {q}\nReference: {ref}\nResponse: {got}\n"
        "Return ONLY a number."
    )
    return {"key": "similarity", "score": _ask_judge(prompt)}

def eval_correctness_rubric(inputs: dict, reference_outputs: dict, outputs: dict):
    filled = (
        CORRECTNESS_PROMPT
        .replace("{{inputs}}", str(inputs))
        .replace("{{outputs}}", str(outputs))
        .replace("{{reference_outputs}}", str(reference_outputs))
    )
    prompt = (
        "Read the following rubric-driven evaluation and return a single integer score 1–10.\n\n"
        f"{filled}\n\nReturn ONLY the number."
    )
    return {"key": "correctness", "score": _ask_judge(prompt)}

def eval_helpfulness(inputs: dict, reference_outputs: dict, outputs: dict):
    q = inputs.get("HUMAN", "")
    got = outputs.get("output", "")
    prompt = (
        "Evaluate HELPFULNESS on a scale 1–10 (10 = fully helpful, actionable, "
        "addresses the request, minimal irrelevant content). Consider clarity and guidance.\n\n"
        f"Question: {q}\nResponse: {got}\nReturn ONLY a number."
    )
    return {"key": "helpfulness", "score": _ask_judge(prompt)}

def eval_reference_containment(inputs: dict, reference_outputs: dict, outputs: dict):
    """Simple rule-based: token overlap of reference in response."""
    ref = reference_outputs.get("AI", "").strip().lower()
    got = outputs.get("output", "").strip().lower()
    if not ref or not got:
        return {"key": "containment", "score": 1}
    ref_toks = set(re.findall(r"\w+", ref))
    got_toks = set(re.findall(r"\w+", got))
    if not ref_toks:
        return {"key": "containment", "score": 1}
    overlap = len(ref_toks & got_toks) / len(ref_toks)
    score = max(1, min(10, int(round(overlap * 10))))
    return {"key": "containment", "score": score}

EVALUATORS = [
    eval_semantic_similarity,
    eval_correctness_rubric,
    eval_helpfulness,
    eval_reference_containment,
]

# ---------- Local summary (immediate feedback) ----------
def _summarize_local(examples) -> Tuple[Dict[str, float], List[Dict]]:
    per_example = []
    keys = ["similarity", "correctness", "helpfulness", "containment"]
    acc = {k: [] for k in keys}

    for ex in examples:
        inputs = ex.inputs
        refs = ex.outputs
        out = target_function(inputs)
        row = {"question": inputs.get("HUMAN", ""), "response": out.get("output", "")}
        for ev in EVALUATORS:
            res = ev(inputs, refs, out)
            row[res["key"]] = res["score"]
            acc[res["key"]].append(res["score"])
        per_example.append(row)

    means = {k: (statistics.mean(v) if v else 0.0) for k, v in acc.items()}
    return means, per_example

if __name__ == "__main__":
    # Pull dataset examples
    examples = list(client.list_examples(dataset_id=DATASET_ID))

    # 1) Local immediate summary
    means, rows = _summarize_local(examples)
    print("\n=== Local Evaluation Summary (Immediate) ===")
    print(f"Similarity : {means['similarity']:.2f}/10")
    print(f"Correctness: {means['correctness']:.2f}/10")
    print(f"Helpfulness: {means['helpfulness']:.2f}/10")
    print(f"Containment: {means['containment']:.2f}/10")

    # Optional per-example compact printout
    for r in rows:
        print(f"- Q: {r['question']}\n  → sim={r['similarity']}, corr={r['correctness']}, help={r['helpfulness']}, cont={r['containment']}")

    # 2) LangSmith SDK experiment (for traceability + UI)
    results = client.evaluate(
        target_function,
        data=examples,
        evaluators=EVALUATORS,
        experiment_prefix=f"BookNook-{GEMINI_MODEL}",
        description=f"Book Nook — multi-criteria eval (similarity, correctness, helpfulness, containment) on {GEMINI_MODEL}",
        max_concurrency=4,
    )
    url = getattr(results, "results_url", None) or getattr(results, "url", None)
    if url:
        print("\n✅ View the LangSmith evaluation results at:")
        print(url)
