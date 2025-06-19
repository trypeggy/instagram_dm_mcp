# Instagram DM MCP server

This is a Model Context Protocol (MCP) server for sending instagram DMs

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

## Feedback

Your feedback will be massively appreciated. Please [tell us](mailto:feedback@usegala.com) which features on that list you like to see next or request entirely new ones.

---

## License

This project is licensed under the MIT License.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)
