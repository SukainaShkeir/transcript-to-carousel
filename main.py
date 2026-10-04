import json
import os
from langgraph.graph import StateGraph, START, END

from state import CarouselState
from guards import input_guard, human_approval
from agents.content_writer import content_writer
from agents.prompt_writer import prompt_writer
from agents.designer import designer


# Decide where to go after the human answers
def route_after_approval(state):
    return "designer" if state["approved"] else END


# 1. Build the graph
builder = StateGraph(CarouselState)

builder.add_node("input_guard", input_guard)
builder.add_node("content_writer", content_writer)
builder.add_node("prompt_writer", prompt_writer)
builder.add_node("human_approval", human_approval)
builder.add_node("designer", designer)

builder.add_edge(START, "input_guard")
builder.add_edge("input_guard", "content_writer")
builder.add_edge("content_writer", "prompt_writer")
builder.add_edge("prompt_writer", "human_approval")
builder.add_conditional_edges("human_approval", route_after_approval)
builder.add_edge("designer", END)

graph = builder.compile()

# 2. Run it
if __name__ == "__main__":
    with open("transcripts/sample.txt", encoding="utf-8") as f:
        transcript = f.read()

    final_state = graph.invoke({"transcript": transcript})

    # 3. Save the results for you (Canva) and for evaluation
    os.makedirs("output", exist_ok=True)
    results = {k: v for k, v in final_state.items() if k != "transcript"}
    with open("output/results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

        # 4. Short summary in the terminal
    print(f"\nLanguage: {final_state['language']}")
    print(f"Slides: {len(final_state['slide_texts'])}")
    if final_state["approved"]:
        print(f"Designer attempts: {final_state['attempts']}")
        flagged = final_state["flagged_slides"]
        if flagged:
            print(f"⚠ Needs human review: slides {flagged}")
        else:
            print("All slides passed review.")
    else:
        print("Images not generated (not approved).")
    print("Saved: output/results.json")