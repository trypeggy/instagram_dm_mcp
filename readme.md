# Instagram DM MCP server

This is a Model Context Protocol (MCP) server for sending instagram Direct Messages.

With this you can send Instagram Direct Messages from your account (more capabilities coming soon).

Here's an example of what you can do when it's connected to Claude.


https://github.com/user-attachments/assets/9c945f25-4484-4223-8d6b-5bf31243464c


> To get updates on this and other projects we work on [enter your email here](https://tally.so/r/np6rYy)

PS: Join our [Twitter community](https://twitter.com/i/communities/1937504082635170114) for all things MCP 

---

## Hackathon Submission

Build anything using this Instagram DM MCP (can be technical, no-code or low-code) and submit!

No restrictions, open to anyone/anywhere to join.

<div align="left">

[![Submit now](https://img.shields.io/badge/Submit%20now-black?style=for-the-badge&logo=tally&logoColor=white&labelColor=000000&color=000000&size=large)](https://tally.so/r/mR18zl)

</div>

> Note: submisions due by Friday 27 June 11:59PM PST

### Three cash prizes up for grabs

1. $5k USD - Breaking the internet (go viral AF)
2. $2.5k USD - Technical Sorcery (coolest technical implementation)
3. $2.5k USD - Holy Sh*t Award (make our jaws drop)

---

## Installation

### Prerequisites

- Python 3.11+
- Anthropic Claude Desktop app (or Cursor)
- Pip (Python package manager), install with `python -m pip install`
- An instagram account

### Steps

1. **Clone this repository**

   ```bash
   git clone https://github.com/trypeggy/instagram_dm_mcp.git
   cd instagram_dm_mcp
   ```

2. **Install dependencies**

  - Using uv (recommended):
    ```bash
    uv sync
    ```
  - Using Pip:
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure Instagram credentials**

   You have two options for providing your Instagram credentials:

   **Option A: Environment Variables (Recommended)**
   
   **Quick Setup (Recommended):**
   
   Run the helper script:
   
   ```bash
   python setup_env.py
   ```
   
   This will interactively prompt you for your credentials and create the `.env` file securely.
   
   **Manual Setup:**
   
   Create a `.env` file in the project root:
   
   ```bash
   cp env.example .env
   ```
   
   Then edit `.env` with your actual credentials:
   
   ```
   INSTAGRAM_USERNAME=your_instagram_username
   INSTAGRAM_PASSWORD=your_instagram_password
   ```
   
   **Option B: Command Line Arguments**
   
   You can still pass credentials as command line arguments (less secure).

4. **Connect to the MCP server**

   **For Claude Desktop:**
   
   Save this as `claude_desktop_config.json` in your Claude Desktop configuration directory at:

   ```
   ~/Library/Application Support/Claude/claude_desktop_config.json
   ```

   **For Cursor:**
   
   Save this as `mcp.json` in your Cursor configuration directory at:

   ```
   ~/.cursor/mcp.json
   ```

   **Configuration with Environment Variables (Recommended):**
   - Using uv
   
   ```json
   {
     "mcpServers": {
       "instagram_dms": {
           "command": "uv",
           "args": [
             "run",
             "--directory",
             "PATH/TO/instagram_dm_mcp",
             "python",
             "src/mcp_server.py"
           ]
        }
      }
    }
   ```

   - Using Python
    ```json
    {
      "mcpServers": {
        "instagram_dms": {
          "command": "python",
          "args": [
            "{{PATH_TO_SRC}}/instagram_dm_mcp/src/ mcp_server.py"
          ]
        }
      }
    }
    ```

   **Configuration with Command Line Arguments:**
   
   ```json
   {
     "mcpServers": {
       "instagram_dms": {
         "command": "python",
         "args": [
           "{{PATH_TO_SRC}}/instagram_dm_mcp/src/mcp_server.py",
           "--username",
           "{{YOUR_INSTAGRAM_USERNAME}}",
          "--password",
          "{{YOUR_INSTAGRAM_PASSWORD}}"
         ]
       }
     }
   }
   ```

5. **Restart Claude Desktop / Cursor**
   
   Open Claude Desktop and you should now see the Instagram DM MCP as an available integration.

   Or restart Cursor.
---

## Usage

Below is a list of all available tools and what they do:

| Tool Name                   | Description                                                                                   |
|-----------------------------|-----------------------------------------------------------------------------------------------|
| `send_message`              | Send an Instagram direct message to a user by username.                                       |
| `send_photo_message`        | Send a photo as an Instagram direct message to a user by username.                            |
| `send_video_message`        | Send a video as an Instagram direct message to a user by username.                            |
| `list_chats`                | Get Instagram Direct Message threads (chats) from your account, with optional filters/limits.  |
| `list_messages`             | Get messages from a specific Instagram Direct Message thread by thread ID. Now exposes `item_type` and shared post/reel info for each message. Use this to determine which download tool to use. |
| `download_media_from_message` | Download a direct-uploaded photo or video from a DM message (not for shared posts/reels/clips). |
| `download_shared_post_from_message` | Download media from a shared post, reel, or clip in a DM message (not for direct uploads). |
| `list_media_messages`       | List all messages containing direct-uploaded media (photo/video) in a DM thread.              |
| `mark_message_seen`         | Mark a specific message in an Instagram Direct Message thread as seen.                         |
| `list_pending_chats`        | Get Instagram Direct Message threads from your pending inbox.                                  |
| `search_threads`            | Search Instagram Direct Message threads by username or keyword.                                |
| `get_thread_by_participants`| Get an Instagram Direct Message thread by participant user IDs.                                |
| `get_thread_details`        | Get details and messages for a specific Instagram Direct Message thread by thread ID.          |
| `get_user_id_from_username` | Get the Instagram user ID for a given username.                                                |
| `get_username_from_user_id` | Get the Instagram username for a given user ID.                                                |
| `get_user_info`             | Get information about a specific Instagram user by username.                        |
| `search_users`              | Search for Instagram users by username                                              |
| `get_user_stories`          | Get recent stories from a specific Instagram user by username.                                  |
| `like_media`               | Like or unlike a specific media post by media ID.                                                       |
| `get_user_followers`        | Get a list of followers for a specific Instagram user by username.                             |
| `get_user_following`        | Get a list of users that a specific Instagram user is following by username.                   |
| `get_user_posts`            | Get recent posts from a specific Instagram user by username.                                   |


---

## Troubleshooting

For additional Claude Desktop integration troubleshooting, see the [MCP documentation](https://modelcontextprotocol.io/quickstart/server#claude-for-desktop-integration-issues). The documentation includes helpful tips for checking logs and resolving common issues.

---

## Feedback

Your feedback will be massively appreciated. Please [tell us](mailto:tanmay@usegala.com) which features on that list you like to see next or request entirely new ones.

---

## License

This project is licensed under the MIT License.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)
