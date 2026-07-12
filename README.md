# Odoo AI Chatbot

A powerful, agentic AI Chatbot integrated directly into your Odoo ERP. Built using **LangChain** and **OWL**, this module brings an intelligent assistant to your Odoo environment that can interact with your database, query information, and perform operations on your behalf—all while strictly respecting Odoo's native access rights and security models.

---

## 🌟 Key Features

* **Universal Systray Integration**: The chatbot is accessible from anywhere in the Odoo backend via a sleek, modern OWL component in the systray.
* **Agentic Tooling**: The AI doesn't just chat; it *acts*. It is equipped with 6 custom tools to perform real operations on your Odoo database:
  1. `get_model_schema`: Understands your Odoo models and fields dynamically.
  2. `read_odoo_records`: Searches and retrieves data.
  3. `create_odoo_record`: Creates new records.
  4. `update_odoo_records`: Updates existing records.
  5. `delete_odoo_records`: Deletes records safely.
  6. `update_odoo_record_translations`: A native Odoo 16+ JSONB translation tool to update field translations across multiple languages instantly.
* **Strict Security**: Every single tool operation enforces `check_access` / `check_access_rights`. The AI acts strictly as the logged-in user and cannot bypass Odoo's security policies.
* **Multi-Provider Support**: Seamlessly switch between different LLM providers from the Odoo Settings:
  * **Amazon Bedrock** (e.g., Anthropic Claude 3)
  * **Ollama** (Local models like Llama 3 for complete privacy)
* **Contextual Formatting**: The AI natively formats Odoo records into clickable HTML links that route you directly to the correct form views (compatible with Odoo 17/18/19 URL structures).

---

## 🛠️ Technical Stack

* **Backend**: Python, Odoo 17/18/19 API
* **Frontend**: Odoo OWL (Odoo Web Library), JavaScript, SCSS
* **AI Framework**: LangChain, LangGraph

---

## 📦 Installation

1. **Clone the Repository**:
   Place the `odoo_ai_chatbot` directory inside your Odoo `addons` path.
2. **Install Python Dependencies**:
   The module requires LangChain and Boto3 (if using Bedrock). Run:
   ```bash
   pip install langchain langchain-community langchain-aws langgraph boto3
   ```
3. **Install the Module**:
   Restart your Odoo server, go to **Apps**, click **Update Apps List**, search for "AI Chatbot", and click **Activate**.

---

## ⚙️ Configuration

Once installed, navigate to **Settings > General Settings > AI Chatbot Configuration**:

1. **AI Provider**: Choose between `Amazon Bedrock` or `Ollama`.
2. **Provider Settings**:
   * *Bedrock*: Provide your AWS Access Key, Secret Key, Region, and Model ID (e.g., `anthropic.claude-3-haiku-20240307-v1:0`).
   * *Ollama*: Provide your Ollama Base URL (e.g., `http://localhost:11434`) and Model Name (e.g., `llama3`).
3. **System Prompt**: Customize the core instructions given to the AI. (Default rules are provided to ensure stable formatting and strict adherence to available tools).
4. **Theme**: Customize the accent color of the chat widget.

---

## 🛡️ Security & Privacy

This module is designed with enterprise security in mind:
* **No Database Scraping**: The AI only fetches data exactly when prompted by the user through explicitly defined tools.
* **Access Rights**: The AI cannot read, write, or delete any record the active user does not have permission to access. If it tries, Odoo's native `AccessError` blocks it and the AI politely informs the user.

---

## 🚀 Future Roadmap

* **Context-Aware Chat**: Automatically inject the user's active Odoo view/URL context into the chat so the AI knows exactly what record is on the screen without having to be explicitly told.
* **Human-in-the-Loop**: Require explicit human approval before the AI can execute potentially destructive actions like `delete_odoo_records`.
* **Session Summarization**: Condense long chat histories using LLMs to save context windows while maintaining conversational memory.

---

**Created by [Tarang Kushwaha](https://tarang7651.github.io/)**
# odoo_ai_chatbot
