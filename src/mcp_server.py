from fastmcp import FastMCP
from instagrapi import Client
import argparse
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

INSTRUCTIONS = """
This server is used to send messages to a user on Instagram.
"""

client = Client()

mcp_server = FastMCP(
   name="Instagram DMs",
   instructions=INSTRUCTIONS
)


@mcp_server.tool()
def send_message(username: str, message: str) -> Dict[str, Any]:
    """Send an Instagram direct message to a user by username.

    Args:
        username: Instagram username of the recipient.
        message: The message text to send.
    Returns:
        A dictionary with success status and a status message.
    """
    if not username or not message:
        return {"success": False, "message": "Username and message must be provided."}
    try:
        user_id = client.user_id_from_username(username)
        if not user_id:
            return {"success": False, "message": f"User '{username}' not found."}
        dm = client.direct_send(message, [user_id])
        if dm:
            return {"success": True, "message": "Message sent to user.", "direct_message_id": getattr(dm, 'id', None)}
        else:
            return {"success": False, "message": "Failed to send message."}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp_server.tool()
def list_chats(
    amount: int = 20,
    selected_filter: str = "",
    thread_message_limit: Optional[int] = None,
    full: bool = False,
    fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Get Instagram Direct Message threads (chats) from the user's account, with optional filters and limits.

    Args:
        amount: Number of threads to fetch (default 20).
        selected_filter: Filter for threads ("", "flagged", or "unread").
        thread_message_limit: Limit for messages per thread.
        full: If True, return the full thread object for each chat (default False).
        fields: If provided, return only these fields for each thread.
    Returns:
        A dictionary with success status and the list of threads or error message.
    """
    def thread_summary(thread):
        t = thread if isinstance(thread, dict) else thread.dict()
        users = t.get("users", [])
        user_summaries = [
            {
                "username": u.get("username"),
                "full_name": u.get("full_name"),
                "pk": u.get("pk")
            }
            for u in users
        ]
        return {
            "thread_id": t.get("id"),
            "thread_title": t.get("thread_title"),
            "users": user_summaries,
            "last_activity_at": t.get("last_activity_at"),
            "last_message": t.get("messages", [{}])[-1] if t.get("messages") else None
        }

    def filter_fields(thread, fields):
        t = thread if isinstance(thread, dict) else thread.dict()
        return {field: t.get(field) for field in fields}

    try:
        threads = client.direct_threads(amount, selected_filter, thread_message_limit)
        if full:
            return {"success": True, "threads": [t.dict() if hasattr(t, 'dict') else str(t) for t in threads]}
        elif fields:
            return {"success": True, "threads": [filter_fields(t, fields) for t in threads]}
        else:
            return {"success": True, "threads": [thread_summary(t) for t in threads]}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp_server.tool()
def list_messages(thread_id: str, amount: int = 20) -> Dict[str, Any]:
    """Get messages from a specific Instagram Direct Message thread by thread ID, with an optional limit.

    Args:
        thread_id: The thread ID to fetch messages from.
        amount: Number of messages to fetch (default 20).
    Returns:
        A dictionary with success status and the list of messages or error message.
    """
    if not thread_id:
        return {"success": False, "message": "Thread ID must be provided."}
    try:
        messages = client.direct_messages(thread_id, amount)
        return {"success": True, "messages": [m.dict() if hasattr(m, 'dict') else str(m) for m in messages]}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp_server.tool()
def list_pending_chats(amount: int = 20) -> Dict[str, Any]:
    """Get Instagram Direct Message threads (chats) from the user's pending inbox.

    Args:
        amount: Number of pending threads to fetch (default 20).
    Returns:
        A dictionary with success status and the list of pending threads or error message.
    """
    try:
        threads = client.direct_pending_inbox(amount)
        return {"success": True, "threads": [t.dict() if hasattr(t, 'dict') else str(t) for t in threads]}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp_server.tool()
def search_threads(query: str) -> Dict[str, Any]:
    """Search Instagram Direct Message threads by username or keyword.

    Args:
        query: The search term (username or keyword).
    Returns:
        A dictionary with success status and the search results or error message.
    """
    if not query:
        return {"success": False, "message": "Query must be provided."}
    try:
        results = client.direct_search(query)
        return {"success": True, "results": [r.dict() if hasattr(r, 'dict') else str(r) for r in results]}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp_server.tool()
def get_thread_by_participants(user_ids: List[int]) -> Dict[str, Any]:
    """Get an Instagram Direct Message thread by participant user IDs.

    Args:
        user_ids: List of user IDs (ints).
    Returns:
        A dictionary with success status and the thread or error message.
    """
    if not user_ids or not isinstance(user_ids, list):
        return {"success": False, "message": "user_ids must be a non-empty list of user IDs."}
    try:
        thread = client.direct_thread_by_participants(user_ids)
        return {"success": True, "thread": thread.dict() if hasattr(thread, 'dict') else str(thread)}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp_server.tool()
def get_thread_details(thread_id: str, amount: int = 20) -> Dict[str, Any]:
    """Get details and messages for a specific Instagram Direct Message thread by thread ID, with an optional message limit.

    Args:
        thread_id: The thread ID to fetch details for.
        amount: Number of messages to fetch (default 20).
    Returns:
        A dictionary with success status and the thread details or error message.
    """
    if not thread_id:
        return {"success": False, "message": "Thread ID must be provided."}
    try:
        thread = client.direct_thread(thread_id, amount)
        return {"success": True, "thread": thread.dict() if hasattr(thread, 'dict') else str(thread)}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp_server.tool()
def get_user_id_from_username(username: str) -> Dict[str, Any]:
    """Get the Instagram user ID for a given username.

    Args:
        username: Instagram username.
    Returns:
        A dictionary with success status and the user ID or error message.
    """
    if not username:
        return {"success": False, "message": "Username must be provided."}
    try:
        user_id = client.user_id_from_username(username)
        if user_id:
            return {"success": True, "user_id": user_id}
        else:
            return {"success": False, "message": f"User '{username}' not found."}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp_server.tool()
def get_username_from_user_id(user_id: str) -> Dict[str, Any]:
    """Get the Instagram username for a given user ID.

    Args:
        user_id: Instagram user ID.
    Returns:
        A dictionary with success status and the username or error message.
    """
    if not user_id:
        return {"success": False, "message": "User ID must be provided."}
    try:
        username = client.username_from_user_id(user_id)
        if username:
            return {"success": True, "username": username}
        else:
            return {"success": False, "message": f"User ID '{user_id}' not found."}
    except Exception as e:
        return {"success": False, "message": str(e)}


if __name__ == "__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument("--username", type=str, help="Instagram username (can also be set via INSTAGRAM_USERNAME env var)")
   parser.add_argument("--password", type=str, help="Instagram password (can also be set via INSTAGRAM_PASSWORD env var)")
   args = parser.parse_args()

   # Get credentials from environment variables or command line arguments
   username = args.username or os.getenv("INSTAGRAM_USERNAME")
   password = args.password or os.getenv("INSTAGRAM_PASSWORD")

   if not username or not password:
       logger.error("Instagram credentials not provided. Please set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD environment variables in a .env file, or provide --username and --password arguments.")
       print("Error: Instagram credentials not provided.")
       print("Please either:")
       print("1. Create a .env file with INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD")
       print("2. Use --username and --password command line arguments")
       exit(1)

   try:
       logger.info("Attempting to login to Instagram...")
       client.login(username, password)
       logger.info("Successfully logged in to Instagram")
       mcp_server.run(transport="stdio")
   except Exception as e:
       logger.error(f"Failed to login to Instagram: {str(e)}")
       print(f"Error: Failed to login to Instagram - {str(e)}")
       exit(1)
