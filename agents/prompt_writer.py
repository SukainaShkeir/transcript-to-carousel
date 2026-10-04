import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

load_dotenv()

# 1. Load the style guide (long-term memory)
with open("style_guide.md", encoding="utf-8") as f:
    STYLE_GUIDE = f.read()

# Fixed visual rules, added by code to EVERY prompt (guaranteed, not left to the model)
def style_ending(language):
    space = "upper right" if language.lower() == "arabic" else "upper left"
    return (
        " Soft editorial gouache illustration, warm muted earthy palette, soft natural light."
        f" Vertical 4:5 composition with clean empty space in the {space} for text."
        " No text, letters, numbers, or logos anywhere in the image."
    )


# 2. The form: a list of prompts
class PromptPlan(BaseModel):
    image_prompts: list[str] = Field(description="One English image prompt per slide, in the same order")


llm = ChatOpenAI(model=os.getenv("OPENAI_TEXT_MODEL"))
writer = llm.with_structured_output(PromptPlan)

SYSTEM_PROMPT = f"""You are a visual designer writing prompts for an image model.
You receive Instagram carousel slides, their language, and an overall mood.
Rules:
- Write exactly ONE image prompt for EACH slide, in the same order.
- Describe ONLY the scene: who, what, where, what is happening.
- Do NOT mention style, colors, palette, texture, format, layout, or empty space.
  These are added automatically after your prompt.
- Do NOT use symbols or icons (like hearts or signs); show real objects and people.
- Write all prompts in English, even if the slides are in another language.
- Follow the scene guidance below.

{STYLE_GUIDE}"""


# 3. The agent node
def prompt_writer(state):
    slides = "\n".join(
        f"Slide {i + 1}: {text}" for i, text in enumerate(state["slide_texts"])
    )
    user_message = (
        f"Language: {state['language']}\n"
        f"Mood: {state['mood']}\n\n"
        f"Slides:\n{slides}"
    )

    plan = writer.invoke([
        ("system", SYSTEM_PROMPT),
        ("user", user_message),
    ])

    # Safeguard: one prompt per slide
    if len(plan.image_prompts) != len(state["slide_texts"]):
        raise ValueError(
            f"Got {len(plan.image_prompts)} prompts for {len(state['slide_texts'])} slides"
        )

    ending = style_ending(state["language"])
    final_prompts = [p.rstrip(". ") + "." + ending for p in plan.image_prompts]
    return {"image_prompts": final_prompts}

# 4. Test: Agent 1 → Agent 2
if __name__ == "__main__":
    from agents.content_writer import content_writer

    with open("transcripts/sample.txt", encoding="utf-8") as f:
        state = {"transcript": f.read()}

    state.update(content_writer(state))
    state.update(prompt_writer(state))

    for i, (text, prompt) in enumerate(zip(state["slide_texts"], state["image_prompts"]), 1):
        print(f"--- Slide {i} ---")
        print(f"Text:   {text}")
        print(f"Prompt: {prompt}\n")