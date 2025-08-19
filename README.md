# Book Nook — LangGraph Agent with LangSmith Evaluation

This project is my response to the **Sr TSE LangGraph + LangSmith Prompt**.

It demonstrates:
- A **LangGraph-based agent** for a fictional bookstore, *Book Nook*.
- **Custom tools** for book stock lookup and author info.
- A **synthetic dataset** for evaluation.
- A **multi-criteria evaluation** pipeline using LangSmith (SDK + UI).
- A **friction log** to capture what worked, what was confusing, and what could improve.

---

## 🔄 Agent Flow

```mermaid
flowchart TD
    A[User Query] --> B[Chatbot Node]
    B -->|Decide| C[Book Nook Tools]
    C -->|Stock| D[check_stock_availability]
    C -->|Author| E[get_author_info]
    C -->|Other| F[LLM Reasoning]
    D --> G[LLM Response]
    E --> G
    F --> G
    G --> H[Final Answer to User]
```

---

## 📂 Project Structure

```
.
├── agent.py        # Defines LangGraph agent (Book Nook chatbot)
├── tools.py        # Custom Book Nook tools (stock + author info)
├── prompts.py      # System prompt and rubric for correctness eval
├── dataset.py      # Seeds LangSmith dataset with synthetic examples
├── eval.py         # Runs evaluation (local summary + LangSmith)
├── friction.md     # Notes on pain points / feedback
└── requirements.txt
```

---

## 🧩 Script Flow (How the pieces fit)

```mermaid
flowchart LR
    subgraph Repo
      A[tools.py\nBook Nook tools] -->|import| B[agent.py\nLangGraph agent]
      C[prompts.py\nSystem + rubric] -->|import| B
      C -->|import| D[eval.py\nmulti-criteria eval]
      E[dataset.py\nseed examples] -->|creates| F[(LangSmith Dataset\nDATASET_ID)]
      B -->|manual test| G[CLI run]
      D -->|reads examples| F
      D -->|target_function| B
      D -->|results + traces| H[(LangSmith Experiments)]
    end

    style F fill:#eef,stroke:#77f
    style H fill:#efe,stroke:#7a7
```

---

## 📈 Evaluation Sequence (SDK call-by-call)

```mermaid
sequenceDiagram
    autonumber
    participant Dev as You
    participant Eval as eval.py
    participant LS as LangSmith SDK
    participant DS as Dataset (DATASET_ID)
    participant Agent as agent.py (graph)
    participant Tools as tools.py

    Dev->>Eval: python eval.py
    Eval->>LS: list_examples(dataset_id)
    LS-->>Eval: examples[]
    loop For each example
        Eval->>Agent: run_once(HUMAN)
        Agent->>Tools: (if needed) tool invocation(s)
        Tools-->>Agent: tool result
        Agent-->>Eval: final response (output)
        Eval->>Eval: run evaluators (similarity, correctness, helpfulness, containment)
    end
    Eval->>Eval: print local averages (per evaluator)
    Eval->>LS: evaluate(target_function, evaluators, data)
    LS-->>Eval: experiment URL
    Eval-->>Dev: print LangSmith URL
```

---

## 🚀 How to Run

1. **Set environment variables** in `.env`:
   ```env
   LANGSMITH_API_KEY=...
   DATASET_ID=...
   GEMINI_API_KEY=...
   GEMINI_MODEL=gemini-1.5-flash
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Seed dataset**:
   ```bash
   python dataset.py
   ```

4. **Smoke test the agent**:
   ```bash
   python agent.py
   ```

5. **Run evaluation**:
   ```bash
   python eval.py
   ```
   Example output:
   ```
   === Local Evaluation Summary (Immediate) ===
   Similarity : 9.25/10
   Correctness: 9.00/10
   Helpfulness: 8.75/10
   Containment: 8.50/10

   ✅ View the LangSmith evaluation results at:
   https://smith.langchain.com/.../experiments/...
   ```

---

## 📊 What You’ll Share
- **Code snippets / repo link**  
- **Walkthrough (~15min)** covering:
  - What you built  
  - How you evaluated it  
  - What you learned  
  - What might confuse a new user  
- **Friction log** (below)
