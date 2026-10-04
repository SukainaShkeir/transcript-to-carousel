from typing import TypedDict


class CarouselState(TypedDict):
    # Input
    transcript: str

    # Agent 1: Content Writer
    language: str
    slide_count: int
    slide_texts: list[str]
    caption: str
    mood: str
    approved: bool

    # Agent 2: Prompt Writer
    image_prompts: list[str]

    # Agent 3: Designer
    image_paths: list[str]
    review_notes: list[str]
    attempts: int
    flagged_slides: list[int]