from fastmcp import FastMCP
from instagrapi import Client
import argparse
from typing import Optional


INSTRUCTIONS = """
This server is used to send messages to a user on Instagram.
"""

client = Client()

mcp_server = FastMCP(
   name="Instagram DMs",
   instructions=INSTRUCTIONS
)


@mcp_server.tool(
  description="Send a message to a user on Instagram, given their username and a message to send.",
)
def send_instagram_dm(username: str, message: str):
   user_id = client.user_id_from_username(username)
   client.direct_send(message, [user_id])
   return "Message sent to user."


@mcp_server.tool(
   description="Get a list of message threads from the user's Instagram account.",
)
def get_threads(
   amount: int = 20,
   selected_filter: str = "",
   thread_message_limit: Optional[int] = None,
):
   threads = client.direct_threads(amount, selected_filter, thread_message_limit)
   return threads


@mcp_server.tool(
   description="Get a list of messages from a thread.",
)
def get_messages(thread_id: str, amount: int = 20):
   messages = client.direct_messages(thread_id, amount)
   return messages


if __name__ == "__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument("--username", type=str, required=True)
   parser.add_argument("--password", type=str, required=True)
   args = parser.parse_args()

   client.login(args.username, args.password)
   mcp_server.run(transport="stdio")
