# FastAPI Chat Application with Branching

A backend chat service built with FastAPI, supporting conversation branching, user authentication, and dual-database storage (PostgreSQL + MongoDB).

## Features

- Chat Management (create, read, update, delete)
- Message Handling with Branching Support
- User Authentication
- Dual Database Storage (PostgreSQL + MongoDB)
- Caching with Redis
- RESTful API Design

## Prerequisites

- Python 3.8+
- PostgreSQL
- MongoDB
- Redis

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd chat-api-backend
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following variables:
```env
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=chat_db
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=chat_db
REDIS_HOST=localhost
REDIS_PORT=6379
SECRET_KEY=your-secret-key-here
```

5. Initialize the databases:
```bash
# Create PostgreSQL database
createdb chat_db

# Run migrations
alembic upgrade head
```

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

2. The API will be available at `http://localhost:8000`

3. API documentation will be available at:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- POST `/api/v1/auth/login` - Login and get access token

### Chats
- POST `/api/v1/chats/create-chat` - Create a new chat
- GET `/api/v1/chats/get-chat/{chat_id}` - Get chat details and messages
- PUT `/api/v1/chats/update-chat/{chat_id}` - Update chat metadata
- DELETE `/api/v1/chats/delete-chat/{chat_id}` - Delete a chat

### Messages
- POST `/api/v1/messages/add-message` - Add message to a chat
- GET `/api/v1/messages/get-messages/{chat_id}` - Get messages for a chat

### Branches
- POST `/api/v1/branches/create-branch` - Create branch from a message
- GET `/api/v1/branches/get-branches/{chat_id}` - Get all branches for a chat
- PUT `/api/v1/branches/set-active-branch` - Set a specific branch as active

## Testing

Run the test suite:
```bash
pytest
```

## License

MIT 