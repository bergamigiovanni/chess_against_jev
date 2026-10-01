"""JEV adapter for choosing a legal chess move."""

from collections.abc import Mapping, Sequence
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from typesafe_sdk import Choice, TypeSafeClient


def _extract_choice(response: Any, question: str) -> str:
    """Extract a Choice label while tolerating SDK response representations."""
    answers = getattr(response, "answers", None)
    if answers is None and isinstance(response, Mapping):
        answers = response.get("answers")

    answer: Any = answers.get(question) if isinstance(answers, Mapping) else None
    if answer is None:
        choices = getattr(response, "choices", None)
        if isinstance(choices, Mapping):
            answer = choices.get(question)
    if answer is None:
        raise ValueError("JEV returned no choice for the requested question")

    choice = getattr(answer, "choice", answer)
    if isinstance(choice, Sequence) and not isinstance(choice, str):
        if len(choice) != 1:
            raise ValueError("JEV returned multiple choices")
        choice = choice[0]
    if not isinstance(choice, str) or not choice:
        raise ValueError("JEV returned an invalid choice")
    return choice


def jev_choice_request(
    question: str,
    state: Mapping[str, Any],
    instructions: str,
    criteria: Mapping[str, str | None],
) -> str:
    """Ask JEV to select one label from the supplied criteria."""
    print(state)
    print(instructions)
    print(criteria)
    with TypeSafeClient() as client:
        response = client.system_one(
            state=dict(state),
            questions={
                question: Choice(
                    instructions=instructions,
                    criteria=dict(criteria),
                ),
            },
        )
    print(response)
    return _extract_choice(response, question)
