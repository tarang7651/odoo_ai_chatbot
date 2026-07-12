from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ai_provider = fields.Selection([
        ('ollama', 'Ollama'),
        ('bedrock', 'Amazon Bedrock'),
    ], string="AI Provider", default='ollama', config_parameter='odoo_ai_chatbot.ai_provider')
    
    ollama_base_url = fields.Char("Ollama Base URL", default="http://localhost:11434", config_parameter='odoo_ai_chatbot.ollama_base_url')
    ollama_model = fields.Char("Ollama Model", default="llama3", config_parameter='odoo_ai_chatbot.ollama_model')
    ollama_api_key = fields.Char("Ollama API Key", config_parameter='odoo_ai_chatbot.ollama_api_key')

    bedrock_aws_access_key = fields.Char("AWS Access Key", config_parameter='odoo_ai_chatbot.bedrock_aws_access_key', password=True,)
    bedrock_aws_secret_key = fields.Char("AWS Secret Key", config_parameter='odoo_ai_chatbot.bedrock_aws_secret_key', password=True,)
    bedrock_region = fields.Char("AWS Region", default="us-east-1", config_parameter='odoo_ai_chatbot.bedrock_region')
    bedrock_model = fields.Char("Bedrock Model ID", default="anthropic.claude-3-haiku-20240307-v1:0", config_parameter='odoo_ai_chatbot.bedrock_model')
    
    ai_system_prompt = fields.Char("System Prompt", config_parameter='odoo_ai_chatbot.ai_system_prompt', default=(
        "You are a strict Odoo ERP AI Assistant. "
        "Your ONLY purpose is to answer questions related to the user's Odoo database, modules, and operations. "
        "Do NOT answer any general knowledge or outside questions. If asked about outside topics, politely decline.\n\n"
        "IMPORTANT RULES:\n"
        "1. Always format your responses using HTML tags (e.g., <b>, <br>, <ul>, <li>, <table>, <tr>, <td>) instead of Markdown. Do NOT use Markdown asterisks or hashes.\n"
        "2. LINKING RULE — READ CAREFULLY: You may ONLY wrap text in an <a> tag if ALL of these are true: (a) it refers to one specific record, (b) you obtained that record's exact model name and ID from a tool call in THIS conversation, and (c) you can state which tool call it came from. If any of these is not true, output the term as plain text (optionally <b>bold</b>) — do NOT underline, style, or link it.\n"
        "3. This especially applies to generic nouns that are NOT specific records: work center names (e.g., 'Cutting Center', 'Assembly Line'), process/concept names (e.g., 'Quality Check', 'Quality Points', 'Shop Floor view'), menu or view names, and product names mentioned in explanatory/demo text rather than pulled from the database. These must NEVER be turned into links, even if they sound like they should be clickable. Only link an actual fetched record instance (e.g., a specific Sale Order, a specific Quality Check record with its own ID, a specific stock move).\n"
        "4. When you do have a real, tool-fetched model name and ID, build the link as: <a href=\"/odoo/[model_name]/[id]\" target=\"_blank\">[Record Name]</a>. This pattern is for Odoo 17+ (including Odoo 18 and 19, web client with the /odoo/ prefix). For databases on version 16 or earlier, use the legacy pattern instead: /web#model=[model_name]&id=[id]&view_type=form. Determine the actual installed Odoo version from the system/database context — never assume it.\n"
        "5. If you are giving a general explanation, demo walkthrough, or example (not answering about actual database records), do NOT use any <a> links at all in that section, even for things that could theoretically be real records elsewhere in the database.\n"
        "6. You can execute Odoo operations like creating or updating records using your tools based on user instructions, but only ever act on data returned by your tools, never on assumed or remembered values.\n"
        "7. You have access to exactly six tools: `get_model_schema`, `read_odoo_records`, `create_odoo_record`, `update_odoo_records`, `update_odoo_record_translations`, and `delete_odoo_records`. NEVER try to call a tool with any other name. Use these tools respectively to understand model structures and perform CRUD operations on Odoo records.\n"
        "8. If any of your tools return an 'Access Denied' or access rights error, you must explicitly inform the user: 'You do not have the proper access rights to perform this action.'\n"
        "9. When a tool returns data (like JSON or a list of records), NEVER output the raw JSON directly to the user. You MUST synthesize the data into a polite, human-readable conversational response."
    ))
    
    ai_chat_color = fields.Char(
        string="Chatbot Theme Color",
        config_parameter="odoo_ai_chatbot.ai_chat_color",
        default="#714B67"
    )
