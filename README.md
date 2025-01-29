# Vigil: The Adventure-Driven Discord AI Bot 🌟

Vigil is an AI-powered Discord bot with a playful, adventurous personality designed to keep conversations engaging, concise, and boundary-pushing while remaining fun and respectful. Vigil combines cutting-edge AI tools with interactive features to provide a unique user experience — from answering questions to generating custom images.

---

## 🔥 Features

- **Dynamic AI Conversations**: Uses Anthropics Claude AI to generate charming and confident responses, perfectly fitting the mood of any Discord server.
- **Web Search Integration**: Dynamically checks whether a user's query needs additional web information and fetches it using Perplexity AI.
- **Image Generation**: Generates custom AI art via Leonardo AI directly in the chat.
- **Conversation History**: Tracks and saves user interactions for context-aware conversations.

---

## 🚀 Getting Started

Follow these steps to set up and run Vigil on your local machine.

### Prerequisites

Ensure you have the following installed and configured:
- Python 3.10+ 🐍
- A Discord bot token (create one in the [Discord Developer Portal](https://discord.com/developers/applications))
- API keys for:
  - Anthropics Claude AI
  - Perplexity AI
  - Leonardo AI
- `pip` for installing dependencies
- (Optional) Virtual environment setup knowledge

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/vigil.git
   cd vigil
   ```

2. **Set Up a Python Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # For Linux/macOS
   .\venv\Scripts\activate   # For Windows
   ```

3. **Install Required Packages**
   ```bash
   pip install -r requirements.txt
   ```

4. **Add Environment Variables**
   - Create a `.env` file in the root directory and populate it with the required tokens:
     ```env
     DISCORD_TOKEN=your_discord_bot_token
     ANTHROPIC_API_KEY=your_anthropic_api_key
     LEONARDO_API_KEY=your_leonardo_api_key
     PERPLEXITY_API_KEY=your_perplexity_api_key
     DATABASE_URL=postgresql://user:password@host:port/dbname  # Supabase connection string
     ```
   - For Supabase setup:
     1. Create a new project at supabase.com
     2. Go to Database → Settings → Connection String (use Pooling mode)
     3. Run this SQL in the SQL Editor to create tables:
        ```sql
        -- Create short_term_memories table
        CREATE TABLE short_term_memories (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            creation_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expiration_time TIMESTAMPTZ NOT NULL
        );
        
        -- Create index for expiration time
        CREATE INDEX idx_short_term_expiration ON short_term_memories (expiration_time);
        
        -- Create long_term_memories table 
        CREATE TABLE long_term_memories (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            server_id BIGINT,
            type VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            importance INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        
        -- Create composite index for user/server filtering
        CREATE INDEX idx_user_server ON long_term_memories (user_id, server_id);
        ```

---

## 🕹️ Usage

### Running the Bot
To start Vigil, simply run the following command in your terminal:
```bash
python main.py
```

### Interactions
Here's how to interact with Vigil:

#### **Mention Vigil for a Chat**
- Mention Vigil in a message to start a conversation. Example:
  ```
  @Vigil What's the weather in New York?
  ```

#### **Generate an Image**
- Use the `/imagine` command to create an image. Example:
  ```
  /imagine prompt="A futuristic city at night with neon lights"
  ```

#### **Sample Responses**
- Customize responses based on Vigil's playful personality:
  - *"Looking for an answer? Let me check the web for you!"*
  - *"I'd rather charm you than bore you with long answers 😉."*

---


## 🛠️ Technologies Used

- **[discord.py](https://discordpy.readthedocs.io/)**: Interface with Discord's APIs.
- **[Anthropic SDK](https://www.anthropic.com/)**: For AI message generation and contextual conversation support.
- **[python-dotenv](https://pypi.org/project/python-dotenv/)**: Manage environment variables securely.
- **[httpx](https://www.python-httpx.org/)**: Asynchronous HTTP requests for external API integration.
- **[Supabase](https://supabase.com/)**: PostgreSQL database hosting and management.
- **[SQLAlchemy](https://www.sqlalchemy.org/)**: ORM for database interactions and async support.
- **[PostgreSQL](https://www.postgresql.org/)**: Relational database system for memory storage.

---

## 🤝 Contributing

We welcome contributions! To get started:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-your-feature-name`).
3. Make your changes and commit them (`git commit -m 'Add some new feature'`).
4. Push the branch (`git push origin feature-your-feature-name`).
5. Open a pull request.

---


## 🙌 Acknowledgments

Special thanks to:
- The [Discord.py](https://discordpy.readthedocs.io/) community for creating such a robust library.
- The developers behind [Anthropic Claude AI](https://www.anthropic.com/) and [Leonardo AI](https://leonardo.ai/).
- Inspiration from OpenAI and their advancements in conversational AI.

---

Feel free to explore, contribute, and share ideas to make Vigil the best AI agent out there!

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
