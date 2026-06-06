"""Render the LangGraph sub-graphs to PNGs and Mermaid sources.

Outputs (written to ``api/assets/``):

* ``physician_graph.png``  — the physician sub-graph
* ``therapist_graph.png``  — the therapist sub-graph
* ``supervisor_flow.png``  — hand-authored Mermaid for the supervisor
                              + sub-graph layout (the supervisor itself
                              is a function, not a graph)
* ``*.mmd``                — Mermaid source for each

The script only needs the LLM/embedding modules to *import*; it does
not make any LLM calls. We pass a ``MemorySaver`` so the graph compiles
without a real Postgres instance.
"""
from __future__ import annotations

import base64
from pathlib import Path

import requests
from langgraph.checkpoint.memory import MemorySaver

from agents.physician_graph import build_physician_graph
from agents.therapist_graph import build_therapist_graph


ASSETS = Path(__file__).resolve().parent / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

SUPERVISOR_MERMAID = """\
flowchart TD
    Start([POST /diagnosis/doctor_id/]) --> Classifier[Supervisor.classify]
    Classifier -->|physician| P[Physician sub-graph<br/>interrupt_after: collect_history]
    Classifier -->|therapist| T[Therapist sub-graph<br/>interrupt_after: respond]
    P --> P1[check_emergency]
    P1 -->|emergency| PEnd([END — emergency banner])
    P1 --> P2[extract_symptoms]
    P2 --> P3[collect_history]
    P3 -->|stop_questioning| P4[plan_diagnosis]
    P4 --> P5[generate_prescription]
    P5 --> P6[generate_soap_note]
    P6 --> PEnd1([END — soap_note_generated])
    T --> T1[respond]
    T1 -->|stop_questioning| T2[recommend]
    T1 -->|keep asking| TEnd([END — awaiting_reply])
    T2 --> TEnd1([END — recommended])

    classDef sup fill:#1f2937,color:#fff,stroke:#0ea5e9,stroke-width:2px
    classDef phy fill:#0ea5e9,color:#fff,stroke:#0369a1
    classDef ther fill:#22c55e,color:#fff,stroke:#15803d
    classDef term fill:#f3f4f6,color:#111,stroke:#6b7280
    class Classifier sup
    class P,P1,P2,P3,P4,P5,P6,PEnd,PEnd1 phy
    class T,T1,T2,TEnd,TEnd1 ther
"""


def render(name: str, graph) -> None:
    png_path = ASSETS / f"{name}.png"
    mmd_path = ASSETS / f"{name}.mmd"
    graph.get_graph().draw_mermaid_png(output_file_path=str(png_path))
    mmd_path.write_text(graph.get_graph().draw_mermaid())
    print(f"  wrote {png_path.relative_to(ASSETS.parent.parent)}")
    print(f"  wrote {mmd_path.relative_to(ASSETS.parent.parent)}")


def render_supervisor() -> None:
    mmd_path = ASSETS / "supervisor_flow.mmd"
    png_path = ASSETS / "supervisor_flow.png"
    mmd_path.write_text(SUPERVISOR_MERMAID, encoding="utf-8")

    # mermaid.ink renders server-side and returns an image. We base64-
    # encode the Mermaid source into the URL — this is their public API.
    encoded = base64.urlsafe_b64encode(mmd_path.read_bytes()).decode("ascii")
    r = requests.get(f"https://mermaid.ink/img/{encoded}", timeout=30)
    r.raise_for_status()
    png_path.write_bytes(r.content)
    print(f"  wrote {mmd_path.relative_to(ASSETS.parent.parent)}")
    print(f"  wrote {png_path.relative_to(ASSETS.parent.parent)}")


def main() -> None:
    checkpointer = MemorySaver()
    print("Rendering physician sub-graph…")
    render("physician_graph", build_physician_graph(checkpointer))
    print("Rendering therapist sub-graph…")
    render("therapist_graph", build_therapist_graph(checkpointer))
    print("Rendering supervisor flow…")
    render_supervisor()


if __name__ == "__main__":
    main()
