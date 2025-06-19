from fastmcp import FastMCP
from instagrapi import Client
import argparse

INSTRUCTIONS = """
This server is used to send messages to a user on Instagram.
"""

client = Client()

mcp_server = FastMCP(
   name="Instagram DMs",
   instructions=INSTRUCTIONS
)


@mcp_server.tool(
  description="Send a message to a user on Instagram.",
)
def send_instagram_dm(user_id: str, message: str):
   client.direct_send(user_id, message)


if __name__ == "__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument("--username", type=str, required=True)
   parser.add_argument("--password", type=str, required=True)
   args = parser.parse_args()

   client.login(args.username, args.password)
   mcp_server.run(transport="stdio")
