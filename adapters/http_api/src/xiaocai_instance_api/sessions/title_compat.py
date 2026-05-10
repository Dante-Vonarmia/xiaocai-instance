"""FLARE session title compatibility helpers."""

from flare_kernel.session_record_policy import (
    extract_auto_title,
    extract_preview,
    is_default_title,
)

from xiaocai_instance_api.storage.conversation_store import ConversationStore, SessionRecord


async def apply_auto_title_after_exchange(
    *,
    store: ConversationStore,
    user_id: str,
    session_id: str,
    user_message: str,
    assistant_message: str,
) -> SessionRecord | None:
    """Apply FLARE's draft-title policy after xiaocai message writeback.

    This keeps the compatibility bridge aligned with FLARE's session append
    semantics without moving title derivation into transport routes.
    """

    session = await store.get_session_for_user(user_id=user_id, session_id=session_id)
    if session is None:
        return None
    if not is_default_title(session.title):
        return session

    preview = extract_preview(
        user_message=user_message,
        assistant_message=assistant_message,
    )
    next_title = extract_auto_title(user_message) or extract_auto_title(preview)
    if not next_title:
        return session

    return await store.update_session_title(
        user_id=user_id,
        session_id=session_id,
        title=next_title,
    ) or session
