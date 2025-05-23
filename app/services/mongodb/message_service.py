from datetime import datetime
from typing import List, Optional
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING
from bson import Binary

from app.core.config import settings
from app.models.mongodb.message import MongoMessage

class MessageService:
    def __init__(self):
        self.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            uuidRepresentation="standard"
        )
        self.db = self.client[settings.MONGODB_DB]
        self.collection = self.db.messages

    def _serialize_uuid(self, uuid_obj: UUID) -> str:
        return str(uuid_obj)

    def _serialize_message(self, message: MongoMessage) -> dict:
        message_dict = message.model_dump()
        # Convert UUIDs to strings
        message_dict["id"] = self._serialize_uuid(message_dict["id"])
        message_dict["chat_id"] = self._serialize_uuid(message_dict["chat_id"])
        message_dict["sender_id"] = self._serialize_uuid(message_dict["sender_id"])
        if message_dict.get("parent_message_id"):
            message_dict["parent_message_id"] = self._serialize_uuid(message_dict["parent_message_id"])
        return message_dict

    def _deserialize_message(self, message_dict: dict) -> MongoMessage:
        # Ensure updated_at is set to created_at if not present
        if "updated_at" not in message_dict or message_dict["updated_at"] is None:
            message_dict["updated_at"] = message_dict.get("created_at", datetime.utcnow())
        return MongoMessage(**message_dict)

    async def create_message(self, message: MongoMessage) -> MongoMessage:
        message_dict = self._serialize_message(message)
        await self.collection.insert_one(message_dict)
        return message

    async def get_message(self, message_id: UUID) -> Optional[MongoMessage]:
        message_dict = await self.collection.find_one({"id": self._serialize_uuid(message_id)})
        if message_dict:
            return self._deserialize_message(message_dict)
        return None

    async def get_chat_messages(
        self, 
        chat_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[MongoMessage]:
        cursor = self.collection.find(
            {"chat_id": self._serialize_uuid(chat_id), "deleted_at": None}
        ).sort("created_at", DESCENDING).skip(skip).limit(limit)
        
        messages = []
        async for message_dict in cursor:
            messages.append(self._deserialize_message(message_dict))
        return messages

    async def get_message_thread(
        self, 
        chat_id: UUID, 
        message_id: UUID
    ) -> List[MongoMessage]:
        # Get the parent message
        parent_message = await self.get_message(message_id)
        if not parent_message:
            return []

        # Get all replies
        cursor = self.collection.find(
            {
                "chat_id": self._serialize_uuid(chat_id),
                "parent_message_id": self._serialize_uuid(message_id),
                "deleted_at": None
            }
        ).sort("created_at", 1)
        
        replies = []
        async for message_dict in cursor:
            replies.append(self._deserialize_message(message_dict))
        
        return [parent_message] + replies

    async def get_chat_branches(self, chat_id: UUID) -> List[MongoMessage]:
        cursor = self.collection.find(
            {
                "chat_id": self._serialize_uuid(chat_id),
                "parent_message_id": None,
                "deleted_at": None
            }
        ).sort("created_at", DESCENDING)
        
        messages = []
        async for message_dict in cursor:
            messages.append(self._deserialize_message(message_dict))
        return messages

    async def get_message_branch(
        self, 
        chat_id: UUID, 
        message_id: UUID
    ) -> List[MongoMessage]:
        # Get the parent message
        parent_message = await self.get_message(message_id)
        if not parent_message:
            return []

        # Get all messages in the branch
        cursor = self.collection.find(
            {
                "chat_id": self._serialize_uuid(chat_id),
                "parent_message_id": self._serialize_uuid(message_id),
                "deleted_at": None
            }
        ).sort("created_at", 1)
        
        branch_messages = []
        async for message_dict in cursor:
            branch_messages.append(self._deserialize_message(message_dict))
        
        return [parent_message] + branch_messages

    async def update_message(
        self, 
        message_id: UUID, 
        update_data: dict
    ) -> Optional[MongoMessage]:
        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"id": self._serialize_uuid(message_id)},
            {"$set": update_data}
        )
        if result.modified_count:
            return await self.get_message(message_id)
        return None

    async def delete_message(self, message_id: UUID) -> bool:
        result = await self.collection.update_one(
            {"id": self._serialize_uuid(message_id)},
            {"$set": {"deleted_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

message_service = MessageService() 