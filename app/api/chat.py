from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from typing import List
from app.core.security import get_current_user, get_current_active_superuser
from app.models.user import User
from app.models.chat import ChatMessage
from app.websockets import manager
from jose import jwt, JWTError
from app.core.config import settings
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

ADMIN_RECIPIENT_ID = "admin_inbox"

async def get_user_from_token(token: str):
    """Helper to get user from a WebSocket token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        user = await User.find_one(User.email == email)
        return user
    except JWTError:
        return None

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    await websocket.accept()
    user = await get_user_from_token(token)
    if not user:
        await websocket.close(code=1008)
        return

    manager.connect(websocket, user.email)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            recipient = message_data.get("recipient_email")
            if not user.is_superuser:
                recipient = ADMIN_RECIPIENT_ID

            chat_message = ChatMessage(
                sender_email=user.email,
                recipient_email=recipient,
                message=message_data["message"]
            )
            await chat_message.insert()
            
            ws_message = chat_message.dict()
            ws_message["id"] = str(ws_message["id"])
            ws_message["created_at"] = ws_message["created_at"].isoformat()

            if user.is_superuser:
                await manager.send_personal_message(ws_message, recipient)
            else:
                admin_users = await User.find(User.is_superuser == True).to_list()
                admin_emails = [admin.email for admin in admin_users]
                await manager.broadcast_to_admins(ws_message, admin_emails)
            
            # Also send the message back to the sender so their UI updates
            await manager.send_personal_message(ws_message, user.email)

    except WebSocketDisconnect:
        manager.disconnect(websocket, user.email)
        logger.info(f"Client {user.email} disconnected.")
    except Exception as e:
        logger.error(f"Error in websocket for {user.email}: {e}")
        manager.disconnect(websocket, user.email)

@router.get("/history")
async def get_my_chat_history(current_user: User = Depends(get_current_user)):
    """Get the current user's chat history with admins."""
    admin_emails = [u.email for u in await User.find(User.is_superuser == True).to_list()]
    messages = await ChatMessage.find(
        {"$or": [
            {"sender_email": current_user.email, "recipient_email": ADMIN_RECIPIENT_ID},
            {"recipient_email": current_user.email, "sender_email": {"$in": admin_emails}}
        ]}
    ).sort("+created_at").to_list()
    return messages

@router.get("/history/{user_email}")
async def get_user_chat_history_for_admin(user_email: str, current_user: User = Depends(get_current_active_superuser)):
    """(Admin) Get a specific user's chat history."""
    admin_emails = [u.email for u in await User.find(User.is_superuser == True).to_list()]
    messages = await ChatMessage.find(
        {"$or": [
            {"sender_email": user_email, "recipient_email": ADMIN_RECIPIENT_ID},
            {"recipient_email": user_email, "sender_email": {"$in": admin_emails}}
        ]}
    ).sort("+created_at").to_list()
    return messages

@router.get("/conversations")
async def get_conversations(current_user: User = Depends(get_current_active_superuser)):
    """For admins to get a list of users they've chatted with."""
    # This pipeline will group messages by the non-admin participant in the conversation.
    admin_emails = [admin.email for admin in await User.find(User.is_superuser == True).to_list()]
    pipeline = [
        {
            "$group": {
                "_id": {
                    "$cond": [ { "$in": ["$sender_email", admin_emails] }, "$recipient_email", "$sender_email" ]
                }
            }
        },
        {"$match": {"_id": {"$nin": admin_emails + [ADMIN_RECIPIENT_ID]}}},
        {"$group": {"_id": "$_id"}} # Distinct user emails
    ]
    user_emails_cursor = ChatMessage.aggregate(pipeline)
    return [item['_id'] for item in await user_emails_cursor.to_list()]