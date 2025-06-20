# Instagram DM MCP server

This is a Model Context Protocol (MCP) server for sending instagram Direct Messages.

With this you can send Instagram Direct Messages from your account (more capabilities coming soon).

Here's an example of what you can do when it's connected to Claude.

https://github.com/user-attachments/assets/dcc003e0-f74e-48aa-bf45-18ea62ba0091

> To get updates on this and other projects we work on [enter your email here](https://tally.so/r/np6rYy)

## Hackathon Submission

<div align="left">

[![Submit now](https://img.shields.io/badge/Submit%20now-black?style=for-the-badge&logo=tally&logoColor=white&labelColor=000000&color=000000&size=large)](https://tally.so/r/mR18zl)

</div>

> Note: submisions due by Friday 27 June 11:59PM PST

### Three cash prizes up for grabs

1. $5k USD - Breaking the internet (go viral AF)
2. $2.5k USD - Technical Sorcery (coolest technical implementation)
3. $2.5k USD - Holy Sh*t Award (make our jaws drop)

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

2. **Connect to the MCP server**

   Copy the below json with the appropriate `{{PATH}}` values and `{{API KEY}}`:

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

4. **Restart Claude Desktop / Cursor**
   
   Open Claude Desktop and you should now see the Instagram DM MCP as an available integration.

   Or restart Cursor.
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
