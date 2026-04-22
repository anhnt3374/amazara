from sqlalchemy.orm import Session

from app.models.assistant_order_draft import AssistantOrderDraft


def create_draft(
    db: Session,
    *,
    user_id: str,
    conversation_id: str,
    order_payload: dict,
) -> AssistantOrderDraft:
    draft = AssistantOrderDraft(
        user_id=user_id,
        conversation_id=conversation_id,
        order_payload=order_payload,
        used=False,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


def get_draft(
    db: Session,
    draft_id: str,
    *,
    user_id: str,
    conversation_id: str,
) -> AssistantOrderDraft | None:
    return (
        db.query(AssistantOrderDraft)
        .filter(
            AssistantOrderDraft.id == draft_id,
            AssistantOrderDraft.user_id == user_id,
            AssistantOrderDraft.conversation_id == conversation_id,
        )
        .first()
    )


def mark_used(db: Session, draft: AssistantOrderDraft) -> AssistantOrderDraft:
    draft.used = True
    db.commit()
    db.refresh(draft)
    return draft
