from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING
from bson import Binary

from app.core.config import settings
from app.models.mongodb.message import MongoMessage
from app.crud.user import get as get_user

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
        # Ensure all UUIDs are properly serialized
        message_dict["id"] = str(message.id)
        message_dict["chat_id"] = str(message.chat_id)
        message_dict["sender_id"] = str(message.sender_id)
        if message.parent_message_id:
            message_dict["parent_message_id"] = str(message.parent_message_id)
        
        # Insert the message
        await self.collection.insert_one(message_dict)
        
        # Return the original message object
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
        print(f"Getting messages for chat_id: {chat_id}")  # Add logging
        
        # Get root messages (messages without parent)
        cursor = self.collection.find(
            {
                "chat_id": str(chat_id),
                "parent_message_id": None,
                "deleted_at": None
            }
        ).sort("created_at", DESCENDING).skip(skip).limit(limit)
        
        messages = []
        async for message_dict in cursor:
            try:
                # Convert string UUIDs back to UUID objects
                message_dict["id"] = UUID(message_dict["id"])
                message_dict["chat_id"] = UUID(message_dict["chat_id"])
                message_dict["sender_id"] = UUID(message_dict["sender_id"])
                if message_dict.get("parent_message_id"):
                    message_dict["parent_message_id"] = UUID(message_dict["parent_message_id"])
                
                root_message = self._deserialize_message(message_dict)
                
                # Get thread messages for this root message
                thread_cursor = self.collection.find(
                    {
                        "chat_id": str(chat_id),
                        "parent_message_id": str(root_message.id),
                        "deleted_at": None
                    }
                ).sort("created_at", 1)
                
                thread_messages = []
                async for thread_msg in thread_cursor:
                    try:
                        # Convert string UUIDs back to UUID objects
                        thread_msg["id"] = UUID(thread_msg["id"])
                        thread_msg["chat_id"] = UUID(thread_msg["chat_id"])
                        thread_msg["sender_id"] = UUID(thread_msg["sender_id"])
                        if thread_msg.get("parent_message_id"):
                            thread_msg["parent_message_id"] = UUID(thread_msg["parent_message_id"])
                        
                        thread_messages.append(self._deserialize_message(thread_msg))
                    except Exception as e:
                        print(f"Error processing thread message: {str(e)}")  # Add logging
                        continue
                
                # Add thread messages to the root message
                root_message.thread_messages = thread_messages
                messages.append(root_message)
            except Exception as e:
                print(f"Error processing root message: {str(e)}")  # Add logging
                continue
        
        print(f"Found {len(messages)} messages")  # Add logging
        return messages

    async def get_message_with_sender(self, message: MongoMessage, db: Session) -> dict:
        """Get message with sender information."""
        # Get sender information
        sender = get_user(db=db, id=message.sender_id)
        if not sender:
            raise ValueError(f"Sender with ID {message.sender_id} not found")
        
        # Convert message to dict and add sender info
        message_dict = message.model_dump()
        message_dict["sender"] = {
            "id": str(sender.id),
            "username": sender.username,
            "email": sender.email,
            "is_active": sender.is_active,
            "created_at": sender.created_at
        }
        
        # Process thread messages if any
        if message.thread_messages:
            message_dict["thread_messages"] = [
                await self.get_message_with_sender(thread_msg, db)
                for thread_msg in message.thread_messages
            ]
        
        return message_dict

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