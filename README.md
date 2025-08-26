# X (Twitter) MCP server

[![smithery badge](https://smithery.ai/badge/@rafaljanicki/x-twitter-mcp-server)](https://smithery.ai/server/@rafaljanicki/x-twitter-mcp-server)
[![PyPI version](https://badge.fury.io/py/x-twitter-mcp.svg)](https://badge.fury.io/py/x-twitter-mcp)

A Model Context Protocol (MCP) server for interacting with Twitter (X) via AI tools. This server allows you to fetch tweets, post tweets, search Twitter, manage followers, and more, all through natural language commands in AI Tools.

<a href="https://glama.ai/mcp/servers/@rafaljanicki/x-twitter-mcp-server">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@rafaljanicki/x-twitter-mcp-server/badge" alt="X (Twitter) server MCP server" />
</a>

## Features

- Fetch user profiles, followers, and following lists.
- Post, delete, and favorite tweets.
- Search Twitter for tweets and trends.
- Manage bookmarks and timelines.
- Built-in rate limit handling for the Twitter API.
- Uses Twitter API v2 with proper authentication (API keys and tokens), avoiding the username/password hack to minimize the risk of account suspensions.
- Provides a complete implementation of Twitter API v2 endpoints for user management, tweet management, timelines, and search functionality.

## Prerequisites

- **Python 3.10 or higher**: Ensure Python is installed on your system.
- **Twitter Developer Account**: You need API credentials (API Key, API Secret, Access Token, Access Token Secret, and Bearer Token) from the [Twitter Developer Portal](https://developer.twitter.com/).
- Optional: **Claude Desktop**: Download and install the Claude Desktop app from the [Anthropic website](https://www.anthropic.com/).
- Optional: **Node.js** (for MCP integration): Required for running MCP servers in Claude Desktop.
- A package manager like `uv` or `pip` for Python dependencies.

## Installation

### Option 1: Installing via Smithery (Recommended)

To install X (Twitter) MCP server for Claude Desktop automatically via [Smithery](https://smithery.ai/server//x-twitter-mcp-server):

```bash
npx -y @smithery/cli install @rafaljanicki/x-twitter-mcp-server --client claude
```

### Option 2: Install from PyPI
The easiest way to install `x-twitter-mcp` is via PyPI:

```bash
pip install x-twitter-mcp
```

### Option 3: Install from Source
If you prefer to install from the source repository:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/rafaljanicki/x-twitter-mcp-server.git
   cd x-twitter-mcp-server
   ```

2. **Set Up a Virtual Environment** (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   Using `uv` (recommended, as the project uses `uv.lock`):
   ```bash
   uv sync
   ```
   Alternatively, using `pip`:
   ```bash
   pip install .
   ```

4. **Configure Environment Variables**:
    - Create a `.env` file in the project root (you can copy `.env.example` if provided).
    - Add your Twitter API credentials:
      ```
      TWITTER_API_KEY=your_api_key
      TWITTER_API_SECRET=your_api_secret
      TWITTER_ACCESS_TOKEN=your_access_token
      TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
      TWITTER_BEARER_TOKEN=your_bearer_token
      ```

## Running the Server

Preferred transport is Streamable HTTP. Use one of the following:

### Recommended: Streamable HTTP (Docker/Smithery)
Run the server as an HTTP service with Streamable HTTP and SSE endpoints.

1. Build the Docker image:
   ```bash
   docker build -t x-twitter-mcp .
   ```

2. Run the container (Smithery uses PORT; default here is 8081):
   ```bash
   docker run -p 8081:8081 -e PORT=8081 x-twitter-mcp
   ```

3. Endpoints:
   - Streamable HTTP (JSON-RPC over HTTP): `POST http://localhost:8081/mcp`
   - SSE (Server-Sent Events): `GET http://localhost:8081/sse`

4. Pass config per-request (recommended in Smithery) via base64-encoded `config` query parameter. Example config JSON:
   ```json
   {"twitterApiKey":"...","twitterApiSecret":"...","twitterAccessToken":"...","twitterAccessTokenSecret":"...","twitterBearerToken":"..."}
   ```
   Encode and call `initialize`:
   ```bash
   CONFIG_B64=$(printf '%s' '{"twitterApiKey":"YOUR_KEY","twitterApiSecret":"YOUR_SECRET","twitterAccessToken":"YOUR_TOKEN","twitterAccessTokenSecret":"YOUR_TOKEN_SECRET","twitterBearerToken":"YOUR_BEARER"}' | base64)

   curl -sS -X POST "http://localhost:8081/mcp?config=${CONFIG_B64}" \
     -H 'content-type: application/json' \
     -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{"capabilities":{}}}'
   ```

Notes:
- A `POST /` will return 404; use `/mcp` for Streamable HTTP and `/sse` for SSE.
- When deployed via Smithery, `smithery.yaml` is configured for `runtime: container` and `startCommand.type: http`.

### Streamable HTTP (Local, no Docker)
Run the ASGI server directly.

If installed from PyPI:
```bash
python -m x_twitter_mcp.http_server
```

If installed from source with `uv`:
```bash
uv run python -m x_twitter_mcp.http_server
```

Endpoints and config passing are the same as above.

### Legacy STDIO (CLI Script)
The project also exposes a STDIO CLI script `x-twitter-mcp-server` for desktop clients that expect STDIO.

If installed from PyPI:
```bash
x-twitter-mcp-server
```

If installed from source with `uv`:
```bash
uv run x-twitter-mcp-server
```

## Using with Claude Desktop

To use this MCP server with Claude Desktop, you need to configure Claude to connect to the server. Follow these steps:

### Step 1: Install Node.js
Claude Desktop uses Node.js to run MCP servers. If you don’t have Node.js installed:
- Download and install Node.js from [nodejs.org](https://nodejs.org/).
- Verify installation:
  ```bash
  node --version
  ```

### Step 2: Locate Claude Desktop Configuration
Claude Desktop uses a `claude_desktop_config.json` file to configure MCP servers.

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

If the file doesn’t exist, create it.

### Step 3: Configure the MCP Server
Edit `claude_desktop_config.json` to include the `x-twitter-mcp` server. Replace `/path/to/x-twitter-mcp-server` with the actual path to your project directory (if installed from source) or the path to your Python executable (if installed from PyPI).

If installed from PyPI:
```json
{
  "mcpServers": {
    "x-twitter-mcp": {
      "command": "x-twitter-mcp-server",
      "args": [],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "TWITTER_API_KEY": "your_api_key",
        "TWITTER_API_SECRET": "your_api_secret",
        "TWITTER_ACCESS_TOKEN": "your_access_token",
        "TWITTER_ACCESS_TOKEN_SECRET": "your_access_token_secret",
        "TWITTER_BEARER_TOKEN": "your_bearer_token"
      }
    }
  }
}
```

If installed from source with `uv`:
```json
{
  "mcpServers": {
    "x-twitter-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/x-twitter-mcp-server",
        "run",
        "x-twitter-mcp-server"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

- `"command": "x-twitter-mcp-server"`: Uses the CLI script directly if installed from PyPI.
- `"env"`: If installed from PyPI, you may need to provide environment variables directly in the config (since there’s no `.env` file). If installed from source, the `.env` file will be used.
- `"env": {"PYTHONUNBUFFERED": "1"}`: Ensures output is unbuffered for better logging in Claude.

### Step 4: Restart Claude Desktop
- Quit Claude Desktop completely.
- Reopen Claude Desktop to load the new configuration.

### Step 5: Verify Connection
- Open Claude Desktop.
- Look for a hammer or connector icon in the input area (bottom right corner). This indicates MCP tools are available.
- Click the icon to see the available tools from `x-twitter-mcp`, such as `post_tweet`, `search_twitter`, `get_user_profile`, etc.

### Step 6: Test with Claude
You can now interact with Twitter using natural language in Claude Desktop. Here are some example prompts:

- **Fetch a User Profile**:
  ```
  Get the Twitter profile for user ID 123456.
  ```
  Claude will call the `get_user_profile` tool and return the user’s details.

- **Post a Tweet**:
  ```
  Post a tweet saying "Hello from Claude Desktop! #MCP"
  ```
  Claude will use the `post_tweet` tool to post the tweet and confirm the action.

- **Search Twitter**:
  ```
  Search Twitter for recent tweets about AI.
  ```
  Claude will invoke the `search_twitter` tool and return relevant tweets.

- **Get Trends**:
  ```
  What are the current trending topics on Twitter?
  ```
  Claude will use the `get_trends` tool to fetch trending topics.

When prompted, grant Claude permission to use the MCP tools for the chat session.

## Available Tools

Below is a list of all tools provided by the `x-twitter-mcp` server, along with example executions in Claude Desktop using natural language prompts.

### User Management Tools

#### `get_user_profile`
- **Description**: Get detailed profile information for a user.
- **Claude Desktop Example**:
  ```
  Get the Twitter profile for user ID 123456789.
  ```
  Claude will return the user’s profile details, including ID, name, username, profile image URL, and description.

#### `get_user_by_screen_name`
- **Description**: Fetches a user by screen name.
- **Claude Desktop Example**:
  ```
  Get the Twitter user with screen name "example_user".
  ```
  Claude will return the user’s profile details.

#### `get_user_by_id`
- **Description**: Fetches a user by ID.
- **Claude Desktop Example**:
  ```
  Fetch the Twitter user with ID 987654321.
  ```
  Claude will return the user’s profile details.

#### `get_user_followers`
- **Description**: Retrieves a list of followers for a given user.
- **Claude Desktop Example**:
  ```
  Get the followers of user ID 123456789, limit to 50.
  ```
  Claude will return a list of up to 50 followers.

#### `get_user_following`
- **Description**: Retrieves users the given user is following.
- **Claude Desktop Example**:
  ```
  Who is user ID 123456789 following? Limit to 50 users.
  ```
  Claude will return a list of up to 50 users.

#### `get_user_followers_you_know`
- **Description**: Retrieves a list of common followers.
- **Claude Desktop Example**:
  ```
  Get common followers for user ID 123456789, limit to 50.
  ```
  Claude will return a list of up to 50 common followers (simulated by filtering followers).

#### `get_user_subscriptions`
- **Description**: Retrieves a list of users to which the specified user is subscribed.
- **Claude Desktop Example**:
  ```
  Get the subscriptions for user ID 123456789, limit to 50.
  ```
  Claude will return a list of up to 50 users (using following as a proxy for subscriptions).

### Tweet Management Tools

#### `post_tweet`
- **Description**: Post a tweet with optional media, reply, and tags.
- **Claude Desktop Example**:
  ```
  Post a tweet saying "Hello from Claude Desktop! #MCP"
  ```
  Claude will post the tweet and return the tweet details.

#### `delete_tweet`
- **Description**: Delete a tweet by its ID.
- **Claude Desktop Example**:
  ```
  Delete the tweet with ID 123456789012345678.
  ```
  Claude will delete the tweet and confirm the action.

#### `get_tweet_details`
- **Description**: Get detailed information about a specific tweet.
- **Claude Desktop Example**:
  ```
  Get details for tweet ID 123456789012345678.
  ```
  Claude will return the tweet’s details, including ID, text, creation date, and author ID.

#### `create_poll_tweet`
- **Description**: Create a tweet with a poll.
- **Claude Desktop Example**:
  ```
  Create a poll tweet with the question "What's your favorite color?" and options "Red", "Blue", "Green" for 60 minutes.
  ```
  Claude will create the poll tweet and return the tweet details.

#### `vote_on_poll`
- **Description**: Vote on a poll.
- **Claude Desktop Example**:
  ```
  Vote "Blue" on the poll in tweet ID 123456789012345678.
  ```
  Claude will return a mock response (since Twitter API v2 doesn’t support poll voting).

#### `favorite_tweet`
- **Description**: Favorites a tweet.
- **Claude Desktop Example**:
  ```
  Like the tweet with ID 123456789012345678.
  ```
  Claude will favorite the tweet and confirm the action.

#### `unfavorite_tweet`
- **Description**: Unfavorites a tweet.
- **Claude Desktop Example**:
  ```
  Unlike the tweet with ID 123456789012345678.
  ```
  Claude will unfavorite the tweet and confirm the action.

#### `bookmark_tweet`
- **Description**: Adds the tweet to bookmarks.
- **Claude Desktop Example**:
  ```
  Bookmark the tweet with ID 123456789012345678.
  ```
  Claude will bookmark the tweet and confirm the action.

#### `delete_bookmark`
- **Description**: Removes the tweet from bookmarks.
- **Claude Desktop Example**:
  ```
  Remove the bookmark for tweet ID 123456789012345678.
  ```
  Claude will remove the bookmark and confirm the action.

#### `delete_all_bookmarks`
- **Description**: Deletes all bookmarks.
- **Claude Desktop Example**:
  ```
  Delete all my Twitter bookmarks.
  ```
  Claude will delete all bookmarks and confirm the action.

### Timeline & Search Tools

#### `get_timeline`
- **Description**: Get tweets from your home timeline (For You).
- **Claude Desktop Example**:
  ```
  Show my Twitter For You timeline, limit to 20 tweets.
  ```
  Claude will return up to 20 tweets from your For You timeline.

#### `get_latest_timeline`
- **Description**: Get tweets from your home timeline (Following).
- **Claude Desktop Example**:
  ```
  Show my Twitter Following timeline, limit to 20 tweets.
  ```
  Claude will return up to 20 tweets from your Following timeline.

#### `search_twitter`
- **Description**: Search Twitter with a query.
- **Claude Desktop Example**:
  ```
  Search Twitter for recent tweets about AI, limit to 10.
  ```
  Claude will return up to 10 recent tweets about AI.

#### `get_trends`
- **Description**: Retrieves trending topics on Twitter.
- **Claude Desktop Example**:
  ```
  What are the current trending topics on Twitter? Limit to 10.
  ```
  Claude will return up to 10 trending topics.

#### `get_highlights_tweets`
- **Description**: Retrieves highlighted tweets from a user’s timeline.
- **Claude Desktop Example**:
  ```
  Get highlighted tweets from user ID 123456789, limit to 20.
  ```
  Claude will return up to 20 tweets from the user’s timeline (simulated as highlights).

#### `get_user_mentions`
- **Description**: Get tweets mentioning a specific user.
- **Claude Desktop Example**:
  ```
  Get tweets mentioning user ID 123456789, limit to 20.
  ```
  Claude will return up to 20 tweets mentioning the user.

## Troubleshooting

- **Server Not Starting**:
    - Ensure your `.env` file has all required Twitter API credentials (if installed from source).
    - If installed from PyPI, ensure environment variables are set in `claude_desktop_config.json` or your shell.
    - Check the terminal output for errors when running `x-twitter-mcp-server`.
    - Verify that `uv` or your Python executable is correctly installed and accessible.

- **Claude Not Detecting the Server**:
    - Confirm the path in `claude_desktop_config.json` is correct.
    - Ensure the `command` and `args` point to the correct executable and script.
    - Restart Claude Desktop after updating the config file.
    - Check Claude’s Developer Mode logs (Help → Enable Developer Mode → Open MCP Log File) for errors.

- **Rate Limit Errors**:
    - The server includes rate limit handling, but if you hit Twitter API limits, you may need to wait for the reset window (e.g., 15 minutes for tweet actions).

- **Syntax Warnings**:
    - If you see `SyntaxWarning` messages from Tweepy, they are due to docstring issues in Tweepy with Python 3.13. The server includes a warning suppression to handle this.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on the [GitHub repository](https://github.com/rafaljanicki/x-twitter-mcp-server).

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Author

- **Rafal Janicki** - [rafal@kult.io](mailto:rafal@kult.io)