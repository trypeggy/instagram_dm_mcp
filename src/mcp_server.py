from mcp.server.fastmcp import FastMCP
from instagrapi import Client
import argparse
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

INSTRUCTIONS = """
This server is used to send messages to a user on Instagram.
"""

client = Client()

mcp = FastMCP(
   name="Instagram DMs",
   instructions=INSTRUCTIONS
)


@mcp.tool()
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


@mcp.tool()
def send_photo_message(username: str, photo_path: str) -> Dict[str, Any]:
    """Send a photo via Instagram direct message to a user by username.

    Args:
        username: Instagram username of the recipient.
        photo_path: Path to the photo file to send.
        message: Optional message text to accompany the photo.
    Returns:
        A dictionary with success status and a status message.
    """
    if not username or not photo_path:
        return {"success": False, "message": "Username and photo_path must be provided."}
    
    if not os.path.exists(photo_path):
        return {"success": False, "message": f"Photo file not found: {photo_path}"}
    
    try:
        user_id = client.user_id_from_username(username)
        if not user_id:
            return {"success": False, "message": f"User '{username}' not found."}
        
        result = client.direct_send_photo(Path(photo_path), [user_id])
        if result:
            return {"success": True, "message": "Photo sent successfully.", "direct_message_id": getattr(result, 'id', None)}
        else:
            return {"success": False, "message": "Failed to send photo."}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp.tool()
def send_video_message(username: str, video_path: str) -> Dict[str, Any]:
    """Send a video via Instagram direct message to a user by username.

    Args:
        username: Instagram username of the recipient.
        video_path: Path to the video file to send.
    Returns:
        A dictionary with success status and a status message.
    """
    if not username or not video_path:
        return {"success": False, "message": "Username and video_path must be provided."}
    
    if not os.path.exists(video_path):
        return {"success": False, "message": f"Video file not found: {video_path}"}
    
    try:
        user_id = client.user_id_from_username(username)
        if not user_id:
            return {"success": False, "message": f"User '{username}' not found."}

        result = client.direct_send_video(Path(video_path), [user_id])
        if result:
            return {"success": True, "message": "Video sent successfully.", "direct_message_id": getattr(result, 'id', None)}
        else:
            return {"success": False, "message": "Failed to send video."}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp.tool()
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


@mcp.tool()
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
        result_msgs = []
        for m in messages:
            msg = m.dict() if hasattr(m, 'dict') else (m if isinstance(m, dict) else {})
            # Expose item_type and shared post/reel info if present
            item_type = getattr(m, 'item_type', None) or msg.get('item_type')
            shared_info = None
            shared_url = None
            shared_code = None
            if item_type in ["clip", "media_share", "reel_share", "xma_media_share", "post_share"]:
                # Try to extract code/url from known attributes
                clip = getattr(m, 'clip', None) or msg.get('clip')
                media_share = getattr(m, 'media_share', None) or msg.get('media_share')
                xma = getattr(m, 'xma_media_share', None) or msg.get('xma_media_share')
                post_share = getattr(m, 'post_share', None) or msg.get('post_share')
                # Try to get code/url from any of these
                for obj in [clip, media_share, xma, post_share]:
                    if obj:
                        shared_code = obj.get('code') or obj.get('pk')
                        shared_url = obj.get('url') or (f"https://www.instagram.com/reel/{shared_code}/" if shared_code else None)
                        shared_info = obj
                        break
            msg['item_type'] = item_type
            msg['shared_post_info'] = shared_info
            msg['shared_post_url'] = shared_url
            msg['shared_post_code'] = shared_code
            result_msgs.append(msg)
        return {"success": True, "messages": result_msgs}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp.tool()
def mark_message_seen(thread_id: str, message_id: str) -> Dict[str, Any]:
    """Mark a message as seen in a direct message thread.

    Args:
        thread_id: The thread ID containing the message.
        message_id: The ID of the message to mark as seen.
    Returns:
        A dictionary with success status and a status message.
    """
    if not thread_id or not message_id:
        return {"success": False, "message": "Both thread_id and message_id must be provided."}
    
    try:
        result = client.direct_message_seen(int(thread_id), int(message_id))
        if result:
            return {"success": True, "message": "Message marked as seen."}
        else:
            return {"success": False, "message": "Failed to mark message as seen."}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
def get_user_info(username: str) -> Dict[str, Any]:
    """Get detailed information about an Instagram user.

    Args:
        username: Instagram username to get information about.
    Returns:
        A dictionary with success status and user information.
    """
    if not username:
        return {"success": False, "message": "Username must be provided."}
    
    try:
        user = client.user_info_by_username(username)
        if user:
            user_data = {
                "user_id": str(user.pk),
                "username": user.username,
                "full_name": user.full_name,
                "biography": user.biography,
                "follower_count": user.follower_count,
                "following_count": user.following_count,
                "media_count": user.media_count,
                "is_private": user.is_private,
                "is_verified": user.is_verified,
                "profile_pic_url": str(user.profile_pic_url) if user.profile_pic_url else None,
                "external_url": str(user.external_url) if user.external_url else None,
                "category": user.category,
            }
            return {"success": True, "user_info": user_data}
        else:
            return {"success": False, "message": f"User '{username}' not found."}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp.tool()
def check_user_online_status(usernames: List[str]) -> Dict[str, Any]:
    """Check the online status of Instagram users.

    Args:
        usernames: List of Instagram usernames to check status for.
    Returns:
        A dictionary with success status and users' presence information.
    """
    if not usernames or not isinstance(usernames, list):
        return {"success": False, "message": "A list of usernames must be provided."}
    
    try:
        user_ids = []
        username_to_id = {}
        
        # Get user IDs for the usernames
        for username in usernames:
            try:
                user_id = client.user_id_from_username(username)
                if user_id:
                    user_ids.append(int(user_id))
                    username_to_id[user_id] = username
            except:
                continue
        
        if not user_ids:
            return {"success": False, "message": "No valid users found."}
        
        presence_data = client.direct_users_presence(user_ids)
        
        # Convert back to usernames
        result = {}
        for user_id_str, presence in presence_data.items():
            username = username_to_id.get(user_id_str, f"user_{user_id_str}")
            result[username] = presence
        
        return {"success": True, "presence_data": result}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp.tool()
def search_users(query: str) -> Dict[str, Any]:
    """Search for Instagram users by name or username.

    Args:
        query: Search term (name or username).
        count: Maximum number of users to return (default 10, max 50).
    Returns:
        A dictionary with success status and search results.
    """
    if not query:
        return {"success": False, "message": "Search query must be provided."}
    
    try:
        users = client.search_users(query)
        
        user_results = []
        for user in users:
            user_data = {
                "user_id": str(user.pk),
                "username": user.username,
                "full_name": user.full_name,
                "is_private": user.is_private,
                "profile_pic_url": str(user.profile_pic_url) if user.profile_pic_url else None,
                "follower_count": getattr(user, 'follower_count', None),
            }
            user_results.append(user_data)
        
        return {"success": True, "users": user_results, "count": len(user_results)}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp.tool()
def get_user_stories(username: str) -> Dict[str, Any]:
    """Get Instagram stories from a user.

    Args:
        username: Instagram username to get stories from.
    Returns:
        A dictionary with success status and stories information.
    """
    if not username:
        return {"success": False, "message": "Username must be provided."}
    
    try:
        user_id = client.user_id_from_username(username)
        if not user_id:
            return {"success": False, "message": f"User '{username}' not found."}
        
        stories = client.user_stories(user_id)
        
        story_results = []
        for story in stories:
            story_data = {
                "story_id": str(story.pk),
                "media_type": story.media_type,  # 1=photo, 2=video
                "taken_at": str(story.taken_at),
                "user": {
                    "username": story.user.username,
                    "full_name": story.user.full_name,
                    "user_id": str(story.user.pk)
                },
                "media_url": str(story.thumbnail_url) if story.thumbnail_url else None,
            }
            
            if story.media_type == 2 and story.video_url:
                story_data["video_url"] = str(story.video_url)
                story_data["video_duration"] = story.video_duration
            
            story_results.append(story_data)
        
        return {"success": True, "stories": story_results, "count": len(story_results)}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp.tool()
def like_media(media_url: str, like: bool = True) -> Dict[str, Any]:
    """Like or unlike an Instagram post.

    Args:
        media_url: URL of the Instagram post.
        like: True to like, False to unlike the post.
    Returns:
        A dictionary with success status and a status message.
    """
    if not media_url:
        return {"success": False, "message": "Media URL must be provided."}
    
    try:
        media_pk = client.media_pk_from_url(media_url)
        if not media_pk:
            return {"success": False, "message": "Invalid media URL or post not found."}
        
        if like:
            result = client.media_like(media_pk)
            action = "liked"
        else:
            result = client.media_unlike(media_pk)
            action = "unliked"
        
        if result:
            return {"success": True, "message": f"Post {action} successfully."}
        else:
            return {"success": False, "message": f"Failed to {action.rstrip('d')} post."}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp.tool()
def get_user_followers(username: str, count: int = 20) -> Dict[str, Any]:
    """Get followers of an Instagram user.

    Args:
        username: Instagram username to get followers for.
        count: Maximum number of followers to return (default 20).
    Returns:
        A dictionary with success status and followers list.
    """
    if not username:
        return {"success": False, "message": "Username must be provided."}
    
    try:
        user_id = client.user_id_from_username(username)
        if not user_id:
            return {"success": False, "message": f"User '{username}' not found."}
        
        followers = client.user_followers(user_id, amount=count)
        
        follower_results = []
        for follower_id, follower in followers.items():
            follower_data = {
                "user_id": str(follower.pk),
                "username": follower.username,
                "full_name": follower.full_name,
                "is_private": follower.is_private,
                "profile_pic_url": str(follower.profile_pic_url) if follower.profile_pic_url else None,
            }
            follower_results.append(follower_data)
        
        return {"success": True, "followers": follower_results, "count": len(follower_results)}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp.tool()
def get_user_following(username: str, count: int = 20) -> Dict[str, Any]:
    """Get users that an Instagram user is following.

    Args:
        username: Instagram username to get following list for.
        count: Maximum number of following to return (default 20).
    Returns:
        A dictionary with success status and following list.
    """
    if not username:
        return {"success": False, "message": "Username must be provided."}
    
    try:
        user_id = client.user_id_from_username(username)
        if not user_id:
            return {"success": False, "message": f"User '{username}' not found."}
        
        following = client.user_following(user_id, amount=count)
        
        following_results = []
        for following_id, followed_user in following.items():
            following_data = {
                "user_id": str(followed_user.pk),
                "username": followed_user.username,
                "full_name": followed_user.full_name,
                "is_private": followed_user.is_private,
                "profile_pic_url": str(followed_user.profile_pic_url) if followed_user.profile_pic_url else None,
            }
            following_results.append(following_data)
        
        return {"success": True, "following": following_results, "count": len(following_results)}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp.tool()
def get_user_posts(username: str, count: int = 12) -> Dict[str, Any]:
    """Get recent posts from an Instagram user.

    Args:
        username: Instagram username to get posts from.
        count: Maximum number of posts to return (default 12).
    Returns:
        A dictionary with success status and posts list.
    """
    if not username:
        return {"success": False, "message": "Username must be provided."}
    
    try:
        user_id = client.user_id_from_username(username)
        if not user_id:
            return {"success": False, "message": f"User '{username}' not found."}
        
        medias = client.user_medias(user_id, amount=count)
        
        media_results = []
        for media in medias:
            media_data = {
                "media_id": str(media.pk),
                "media_type": media.media_type,  # 1=photo, 2=video, 8=album
                "caption": media.caption_text if media.caption_text else "",
                "like_count": media.like_count,
                "comment_count": media.comment_count,
                "taken_at": str(media.taken_at),
                "media_url": str(media.thumbnail_url) if media.thumbnail_url else None,
            }
            
            if media.media_type == 2 and media.video_url:
                media_data["video_url"] = str(media.video_url)
                media_data["video_duration"] = media.video_duration
            
            media_results.append(media_data)
        
        return {"success": True, "posts": media_results, "count": len(media_results)}
    except Exception as e:
        return {"success": False, "message": str(e)}


def _ensure_download_directory(download_path: str) -> None:
    """Ensure download directory exists."""
    Path(download_path).mkdir(parents=True, exist_ok=True)


def _download_single_media(media, download_path: str) -> str:
    """Download a single media item and return the file path."""
    media_type = media.media_type
    if media_type == 1:  # Photo
        return str(client.photo_download(media.pk, download_path))
    elif media_type == 2:  # Video
        return str(client.video_download(media.pk, download_path))
    else:
        raise ValueError(f"Unsupported media type: {media_type}")


def _find_message_in_thread(thread_id: str, message_id: str):
    """Find a specific message in a thread."""
    messages = client.direct_messages(thread_id, 100)
    return next((m for m in messages if str(m.id) == message_id), None)


@mcp.tool()
def list_media_messages(thread_id: str, limit: int = 100) -> Dict[str, Any]:
    """List all messages containing media in an Instagram direct message thread.
    Args:
        thread_id: The ID of the thread to check for media messages
        limit: Maximum number of messages to check (default 100, max 200)
    Returns:
        A dictionary containing success status and list of all media messages found
    """
    try:
        limit = min(limit, 200)
        messages = client.direct_messages(thread_id, limit)
        media_messages = []
        for message in messages:
            if message.media:
                media_messages.append({
                    "message_id": str(message.id),
                    "media_type": "photo" if message.media.media_type == 1 else "video",
                    "timestamp": str(message.timestamp) if hasattr(message, 'timestamp') else None,
                    "sender_user_id": message.user_id if hasattr(message, 'user_id') else None
                })
        return {
            "success": True,
            "message": f"Found {len(media_messages)} messages with media",
            "total_messages_checked": len(messages),
            "media_messages": media_messages
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to list media messages: {str(e)}"
        }

@mcp.tool()
def download_media_from_message(message_id: str, thread_id: str, download_path: str = "./downloads") -> Dict[str, Any]:
    """Download media from a specific Instagram direct message and get the local file path.
    Args:
        message_id: The ID of the message containing the media
        thread_id: The ID of the thread containing the message
        download_path: Directory to save the downloaded file (default: ./downloads)
    Returns:
        A dictionary containing success status, a status message, and the file path if successful
    """
    try:
        _ensure_download_directory(download_path)
        target_message = _find_message_in_thread(thread_id, message_id)
        if not target_message:
            return {
                "success": False,
                "message": f"Message {message_id} not found in thread {thread_id}"
            }
        if not target_message.media:
            return {
                "success": False,
                "message": "This message does not contain media"
            }
        file_path = _download_single_media(target_message.media, download_path)
        return {
            "success": True,
            "message": "Media downloaded successfully",
            "file_path": file_path,
            "media_type": "photo" if target_message.media.media_type == 1 else "video",
            "message_id": message_id,
            "thread_id": thread_id
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to download media: {str(e)}"
        }


@mcp.tool()
def download_shared_post_from_message(message_id: str, thread_id: str, download_path: str = "./downloads") -> Dict[str, Any]:
    """Download media from a shared post/reel/clip in a DM message and get the local file path.
    Args:
        message_id: The ID of the message containing the shared post/reel/clip
        thread_id: The ID of the thread containing the message
        download_path: Directory to save the downloaded file (default: ./downloads)
    Returns:
        A dictionary containing success status, a status message, and the file path if successful
    """
    try:
        _ensure_download_directory(download_path)
        target_message = _find_message_in_thread(thread_id, message_id)
        if not target_message:
            return {"success": False, "message": f"Message {message_id} not found in thread {thread_id}"}
        item_type = getattr(target_message, 'item_type', None)
        # Extract shared post/reel/clip URL
        shared_url = None
        shared_code = None
        shared_obj = None
        if item_type in ["clip", "media_share", "reel_share", "xma_media_share", "post_share"]:
            for attr in ['clip', 'media_share', 'xma_media_share', 'post_share']:
                obj = getattr(target_message, attr, None)
                if obj:
                    shared_code = obj.get('code') or obj.get('pk')
                    shared_url = obj.get('url') or (f"https://www.instagram.com/reel/{shared_code}/" if shared_code else None)
                    shared_obj = obj
                    break
        if not shared_url:
            return {"success": False, "message": "This message does not contain a supported shared post/reel/clip"}
        # Download using Instagrapi
        try:
            media_pk = client.media_pk_from_url(shared_url)
            media = client.media_info(media_pk)
            if media.media_type == 1:
                file_path = str(client.photo_download(media_pk, download_path))
                media_type = "photo"
            elif media.media_type == 2:
                file_path = str(client.video_download(media_pk, download_path))
                media_type = "video"
            elif media.media_type == 8:  # album
                # Download all items in album
                album_paths = client.album_download(media_pk, download_path)
                file_path = str(album_paths)
                media_type = "album"
            else:
                return {"success": False, "message": f"Unsupported media type: {media.media_type}"}
            return {
                "success": True,
                "message": "Shared post/reel/clip downloaded successfully",
                "file_path": file_path,
                "media_type": media_type,
                "shared_post_url": shared_url,
                "message_id": message_id,
                "thread_id": thread_id
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to download shared post/reel/clip: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Failed to process message: {str(e)}"}


@mcp.tool()
def delete_message(thread_id: str, message_id: str) -> Dict[str, Any]:
    """Delete a message from a direct message thread.

    Args:
        thread_id: The thread ID containing the message.
        message_id: The ID of the message to delete.
    Returns:
        A dictionary with success status and a status message.
    """
    if not thread_id or not message_id:
        return {"success": False, "message": "Both thread_id and message_id must be provided."}
    
    try:
        result = client.direct_message_delete(int(thread_id), int(message_id))
        if result:
            return {"success": True, "message": "Message deleted successfully."}
        else:
            return {"success": False, "message": "Failed to delete message."}
    except Exception as e:
        return {"success": False, "message": str(e)}


@mcp.tool()
def mute_conversation(thread_id: str, mute: bool = True) -> Dict[str, Any]:
    """Mute or unmute a direct message conversation.

    Args:
        thread_id: The thread ID to mute/unmute.
        mute: True to mute, False to unmute the conversation.
    Returns:
        A dictionary with success status and a status message.
    """
    if not thread_id:
        return {"success": False, "message": "Thread ID must be provided."}
    
    try:
        if mute:
            result = client.direct_thread_mute(int(thread_id))
            action = "muted"
        else:
            result = client.direct_thread_unmute(int(thread_id))
            action = "unmuted"
        
        if result:
            return {"success": True, "message": f"Conversation {action} successfully."}
        else:
            return {"success": False, "message": f"Failed to {action.rstrip('d')} conversation."}
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
       
       # CRITICAL FIX: Session file handling for persistent authentication
       # Without this, Instagram login hangs due to rate limiting and security measures
       # Session files allow Instagram to recognize the client and avoid fresh authentication
       # This prevents the MCP server from hanging after "🚀 Attempting to send DM"
       SESSION_FILE = Path(f"{username}_session.json")
       if SESSION_FILE.exists():
           logger.info(f"Loading existing session from {SESSION_FILE}")
           client.load_settings(SESSION_FILE)
       
       client.login(username, password)
       
       # Save session for future use to avoid repeated fresh authentication
       client.dump_settings(SESSION_FILE)
       logger.info(f"Session saved to {SESSION_FILE}")
       
       logger.info("Successfully logged in to Instagram")
       mcp.run(transport="stdio")
   except Exception as e:
       logger.error(f"Failed to login to Instagram: {str(e)}")
       print(f"Error: Failed to login to Instagram - {str(e)}")
       exit(1)
