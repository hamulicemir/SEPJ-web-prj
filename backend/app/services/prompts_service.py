from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import engine
from app.models.db_models import Prompt
from app.models.api_models import PromptCreate, PromptUpdate
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
    query = text(
        """
        SELECT name, content FROM prompts
        WHERE name = ANY(:names) AND version_tag = :version
    """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"names": names, "version": version}).fetchall()
    return {name: content for name, content in rows}


def build_prompt(text: str, types: list[dict], prompts: dict[str, str]) -> str:
    type_lines = [f"'{t['name']}': {t['desc']}" "" for t in types]
    categories_str = "\n".join(type_lines)
    return f"""
{prompts.get('base_prompt', '')}
{prompts.get('task_prompt_incident_classification', '')}
{prompts.get('category_intro_prompt', '')}

{categories_str}

{prompts.get('classify_rules_prompt', '')}
{prompts.get('info_prompt', '')}

{text.strip()}
"""

def get_all_prompts(db: Session):
    return db.query(Prompt).order_by(Prompt.name).all()


def get_prompt_by_id(db: Session, prompt_id):
    return db.query(Prompt).filter(Prompt.id == prompt_id).first()


def create_prompt(db: Session, data: PromptCreate):
    new_prompt = Prompt(
        name=data.name,
        purpose=data.purpose,
        content=data.content,
        version_tag=data.version_tag,
    )
    db.add(new_prompt)
    db.commit()
    db.refresh(new_prompt)
    return new_prompt


def update_prompt(db: Session, prompt_id, data: PromptUpdate):
    prompt = get_prompt_by_id(db, prompt_id)
    if prompt:
        if data.name is not None:
            prompt.name = data.name
        if data.purpose is not None:
            prompt.purpose = data.purpose
        if data.content is not None:
            prompt.content = data.content
        if data.version_tag is not None:
            prompt.version_tag = data.version_tag
        db.commit()
        db.refresh(prompt)
    return prompt


def delete_prompt(db: Session, prompt_id):
    prompt = get_prompt_by_id(db, prompt_id)
    if prompt:
        db.delete(prompt)
        db.commit()
        return True
    return False