from app.crud.user import (
    get,
    get_by_email,
    get_by_username,
    get_multi,
    create,
    update,
    authenticate,
)
from app.crud.chat import (
    get_chat,
    get_multi as get_chats,
    get_user_chats,
    create_chat,
    update_chat,
    delete_chat,
    add_participant,
    remove_participant,
    get_chat_messages,
    fix_chat_participant_status,
    chat as chat_crud,
)
from app.crud.crud_message import message_crud

user = {
    "get": get,
    "get_by_email": get_by_email,
    "get_by_username": get_by_username,
    "get_multi": get_multi,
    "create": create,
    "update": update,
    "authenticate": authenticate,
}

chat = {
    "get_chat": get_chat,
    "get_multi": get_chats,
    "get_user_chats": get_user_chats,
    "create_chat": create_chat,
    "update_chat": update_chat,
    "delete_chat": delete_chat,
    "add_participant": add_participant,
    "remove_participant": remove_participant,
    "get_participant": chat_crud.get_participant,
    "get_chat_messages": get_chat_messages,
    "fix_chat_participant_status": fix_chat_participant_status,
}

message = message_crud

__all__ = ["user", "chat", "message"] 