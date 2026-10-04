import os
import base64
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from mcp_client import get_tool_schemas, call_tools

load_dotenv()

llm = ChatOpenAI(model=os.getenv("OPENAI_TEXT_MODEL"))
llm_with_tools = llm.bind_tools(get_tool_schemas())
ALLOWED_TOOLS = {"generate_slide_image"}
MAX_ATTEMPTS = 3

# ---------- Part 1: run the tool calls the model requests (from 6a) ----------
def run_tool_calls(response):
    calls = []
    for call in response.tool_calls:
        if call["name"] not in ALLOWED_TOOLS:
            raise ValueError(f"Model tried to call an unknown tool: {call['name']}")
        calls.append((call["name"], call["args"]))

    paths = call_tools(calls)  # goes through the MCP server
    return {args["slide_number"]: path for (_, args), path in zip(calls, paths)}
# ---------- Part 2: the reviewer ----------
class Review(BaseModel):
    approved: bool = Field(description="True if the image matches the prompt and contains no text")
    issue: str = Field(description="What is wrong, or 'none'")
    revised_prompt: str = Field(description="An improved English prompt if not approved, else the original prompt")

reviewer = llm.with_structured_output(Review)

REVIEW_PROMPT = """You review images for an Instagram carousel.
Approve the image only if:
- It clearly represents the prompt.
- It contains NO text, letters, or numbers.
If not approved, explain the issue and write an improved prompt."""

def review_image(path, prompt):
    with open(path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode()
    return reviewer.invoke([
        SystemMessage(REVIEW_PROMPT),
        HumanMessage(content=[
            {"type": "text", "text": f"Prompt: {prompt}"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
        ]),
    ])

# ---------- Part 3: the Designer agent ----------
SYSTEM_PROMPT = """You are a designer producing images for an Instagram carousel.
For EACH slide you receive, call the generate_slide_image tool once,
using the prompt exactly as given and the correct slide number."""

def ask_designer(slides_text):
    response = llm_with_tools.invoke([("system", SYSTEM_PROMPT), ("user", slides_text)])
    return run_tool_calls(response)

def designer(state):
    prompts = list(state["image_prompts"])

    # First generation: all slides
    all_slides = "\n".join(f"Slide {i + 1}: {p}" for i, p in enumerate(prompts))
    images = ask_designer(all_slides)
    attempts = 1
    notes = []

    while True:
        # Review every image
        failed = {}
        for n, path in images.items():
            review = review_image(path, prompts[n - 1])
            if not review.approved:
                failed[n] = review.revised_prompt
                notes.append(f"Attempt {attempts}, slide {n}: {review.issue}")

        # Stop if all passed or out of attempts
        if not failed or attempts >= MAX_ATTEMPTS:
            break

        # Regenerate ONLY the failed slides, with improved prompts
        for n, new_prompt in failed.items():
            prompts[n - 1] = new_prompt
        retry = "\n".join(f"Slide {n}: {p}" for n, p in failed.items())
        images.update(ask_designer(retry))
        attempts += 1

    if len(images) != len(prompts):
        raise ValueError(f"Got {len(images)} images for {len(prompts)} slides")

    return {
        "image_paths": [images[n] for n in sorted(images)],
        "image_prompts": prompts,
        "review_notes": notes,
        "attempts": attempts,
        "flagged_slides": sorted(failed),  # slides still failing after the last review
    }

# ---------- Test ----------
if __name__ == "__main__":
    test_state = {"image_prompts": [
        "A calm mountain at sunrise",
        "A person writing in a journal",
    ]}
    result = designer(test_state)
    for key, value in result.items():
        print(f"{key}: {value}\n")