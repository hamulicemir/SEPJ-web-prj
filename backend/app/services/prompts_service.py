# app/services/prompts_service.py
from sqlalchemy import text
from app.db.session import engine
import logging

logger = logging.getLogger(__name__)

def load_prompts(version="v1") -> dict[str, str]:
    names = [
        "base_prompt",
        "task_prompt_incident_classification",
        "category_intro_prompt",
        "classify_rules_prompt",
        "info_prompt",
    ]

    query = text("""
        SELECT name, content FROM prompts
        WHERE name = ANY(:names) AND version_tag = :version
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"names": names, "version": version}).fetchall()

    result = {name: content for name, content in rows}

    return result

def build_prompt(text: str, types: list[dict], prompts: dict[str, str]) -> str:
    type_lines = [f"'{t['name']}': {t['desc']}""" for t in types]

    categories_str = "\n".join(type_lines)

    return f"""
{prompts['base_prompt']}
{prompts['task_prompt_incident_classification']}
{prompts['category_intro_prompt']}

{categories_str}

{prompts['classify_rules_prompt']}
{prompts['info_prompt']}

{text.strip()}
"""