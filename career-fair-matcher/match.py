import base64
import json
import sys

import anthropic
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv
load_dotenv()


# --- What we expect back from the AI (Pydantic checks this) ---
class RoleMatch(BaseModel):
    role: str
    fit: str  # "strong", "medium", or "weak"
    reason: str


class MatchResult(BaseModel):
    name: str
    email: str | None
    top_matches: list[RoleMatch]


def load_resume(path: str) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def load_roles(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


PROMPT = """You are helping a recruiter at a career fair.
Below are the company's open roles. Read the attached resume and decide
which roles this person fits best.

Rules:
- Rate each role as "strong", "medium", or "weak" fit.
- Pay attention to experience level. Don't call someone a strong fit
  for a senior role if they're entry level.
- Keep each reason to one short sentence.
- Order top_matches from best fit to worst.

Respond with ONLY JSON in exactly this shape, no other text:
{{"name": "...", "email": "... or null", "top_matches": [{{"role": "...", "fit": "...", "reason": "..."}}]}}

Open roles:
{roles}
"""


def match_resume(pdf_bytes: bytes, roles_text: str) -> MatchResult:
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY automatically

    response = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": base64.standard_b64encode(pdf_bytes).decode("utf-8"),
                        },
                    },
                    {"type": "text", "text": PROMPT.format(roles=roles_text)},
                ],
            }
        ],
    )

    text = response.content[0].text.strip()
    text = text.removeprefix("```json").removesuffix("```").strip()

    return MatchResult.model_validate(json.loads(text))
def match(resume_path: str, roles_path: str) -> MatchResult:
    with open(resume_path, "rb") as f:
        return match_resume(f.read(), load_roles(roles_path))

if __name__ == "__main__":
    resume = sys.argv[1] if len(sys.argv) > 1 else "resume.pdf"
    roles = sys.argv[2] if len(sys.argv) > 2 else "roles.txt"

    try:
        result = match(resume, roles)
    except ValidationError as e:
        print("AI returned the wrong shape:\n", e)
        sys.exit(1)

    print(f"\n{result.name}  ({result.email})\n")
    for m in result.top_matches:
        print(f"[{m.fit.upper():6}] {m.role}\n         {m.reason}\n")