import json
import logging
import os
from odoo import models, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_ollama import ChatOllama
from langchain_aws import ChatBedrockConverse
from langchain_core.tools import tool
import boto3


class AIAgent(models.AbstractModel):
    _name = 'ai.agent'
    _description = 'AI Agent Core logic'

    @api.model
    def process_message(self, session_id, message_content):
        session = self.env['ai.chat.session'].browse(session_id)
        if not session.exists():
            session = self.env['ai.chat.session'].create({})
        
        # Save user message
        self.env['ai.chat.message'].create({
            'session_id': session.id,
            'role': 'user',
            'content': message_content
        })

        llm, tools = self._get_llm_and_tools()
        llm_with_tools = llm.bind_tools(tools)
        
        # Load history
        get_param = self.env['ir.config_parameter'].sudo().get_param
        default_prompt = (
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
        )
        system_prompt = get_param('odoo_ai_chatbot.ai_system_prompt', default_prompt)
        
        try:
            import asyncio
            
            async def run_ai_logic():
                # --- Context Window Management (Summarization) ---
                all_messages = session.message_ids.sorted('create_date')
                unsummarized_msgs = all_messages.filtered(lambda m: not m.is_summarized)
                
                if len(unsummarized_msgs) > 6:
                    msgs_to_summarize = unsummarized_msgs[:-4]
                    if msgs_to_summarize:
                        summary_prompt = (
                            f"Here is the summary of the conversation so far:\n{session.summary or 'No previous summary.'}\n\n"
                            "Please extend the summary by incorporating the following new messages. "
                            "Keep the summary concise and focused on the key points, decisions, and context. "
                            "Do not include pleasantries or conversational filler.\n\n"
                        )
                        for m in msgs_to_summarize:
                            summary_prompt += f"{m.role.capitalize()}: {m.content}\n"
                        
                        try:
                            summary_response = await llm.ainvoke([SystemMessage(content=summary_prompt)])
                            session.summary = summary_response.content
                            msgs_to_summarize.write({'is_summarized': True})
                        except Exception as e:
                            _logger.error(f"Error during summarization: {e}")
                
                # --- Build History ---
                history = [SystemMessage(content=system_prompt)]
                if session.summary:
                    history.append(SystemMessage(content=f"Summary of previous conversation:\n{session.summary}"))
                    
                recent_msgs = session.message_ids.filtered(lambda m: not m.is_summarized).sorted('create_date')
                for msg in recent_msgs:
                    if msg.role == 'user':
                        history.append(HumanMessage(content=msg.content))
                    else:
                        history.append(AIMessage(content=msg.content))

                # Custom tool execution loop (max 5 iterations)
                for _ in range(5):
                    response = await llm_with_tools.ainvoke(history)
                    history.append(response)
                    
                    if getattr(response, 'tool_calls', None):
                        for tool_call in response.tool_calls:
                            target_tool = next((t for t in tools if t.name == tool_call["name"]), None)
                            if target_tool:
                                try:
                                    tool_result = await target_tool.ainvoke(tool_call["args"])
                                    history.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"]))
                                except Exception as e:
                                    history.append(ToolMessage(content=f"Error: {str(e)}", tool_call_id=tool_call["id"]))
                            else:
                                history.append(ToolMessage(content=f"Tool '{tool_call['name']}' not found. Available tools are: get_model_schema, read_odoo_records, create_odoo_record, update_odoo_records, update_odoo_record_translations, delete_odoo_records.", tool_call_id=tool_call["id"]))
                    else:
                        break
                        
                last_content = history[-1].content if history else "Max tool iterations reached."
                if isinstance(last_content, list):
                    return "".join([
                        b.get("text", "") if isinstance(b, dict) else str(b)
                        for b in last_content
                    ])
                else:
                    return str(last_content)

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
            except Exception:
                pass
                
            response_content = asyncio.run(run_ai_logic())
            
        except Exception as e:
            _logger.error(f"Error in LLM execution: {e}")
            response_content = f"Sorry, I encountered an error: {str(e)}"

        # Save assistant message
        self.env['ai.chat.message'].create({
            'session_id': session.id,
            'role': 'assistant',
            'content': response_content
        })

        return {
            'session_id': session.id,
            'response': response_content
        }

    def _get_llm_and_tools(self):
        env = self.env
        
        @tool
        def get_model_schema(model_name: str):
            """
            Get the schema (fields and their types) for an Odoo model.
            Always use this to understand a model's schema before interacting with it.
            """
            try:
                Model = env.get(model_name)
                if Model is None:
                    return f"Model {model_name} not found."
                
                try:
                    if hasattr(Model, 'check_access'):
                        Model.check_access('read')
                    else:
                        Model.check_access_rights('read')
                except Exception as e:
                    return f"Access Denied: Cannot access schema for '{model_name}'. Error: {e}"
                
                ir_model = env['ir.model']._get(model_name)
                
                result = {
                    'model': model_name,
                    'name': ir_model.name if ir_model else model_name,
                    'fields': {
                        field_name: {
                            'type': field.type,
                            'string': field.string,
                            'help': field.help,
                            'relation': field.comodel_name if hasattr(field, 'comodel_name') else None,
                            'required': field.required,
                            'readonly': field.readonly,
                        }
                        for field_name, field in Model._fields.items()
                    }
                }
                return json.dumps(result, default=str)
            except Exception as e:
                return f"Error getting schema: {e}"

        @tool
        def read_odoo_records(model_name: str, domain: list = None, fields: list = None, limit: int = None, offset: int = None):
            """
            Search and read records from an Odoo model.
            domain: list of tuples (e.g. [["is_company", "=", True]])
            fields: list of field names to read.
            limit: maximum number of records to return.
            offset: number of records to skip.
            """
            try:
                Model = env.get(model_name)
                if Model is None:
                    return f"Model {model_name} not found."
                
                domain = domain or []
                try:
                    if hasattr(Model, 'check_access'):
                        Model.check_access('read')
                    else:
                        Model.check_access_rights('read')
                except Exception as e:
                    return f"Access Denied: Cannot read '{model_name}'. Error: {e}"
                
                records = Model.search_read(domain, fields=fields, limit=limit, offset=offset)
                return json.dumps(records, default=str)
            except Exception as e:
                return f"Error reading records: {e}"

        @tool
        def create_odoo_record(model_name: str, values: dict):
            """
            Create a new record in an Odoo model.
            values: dictionary of field values.
            """
            try:
                Model = env.get(model_name)
                if Model is None:
                    return f"Model {model_name} not found."
                
                try:
                    if hasattr(Model, 'check_access'):
                        Model.check_access('create')
                    else:
                        Model.check_access_rights('create')
                except Exception as e:
                    return f"Access Denied: Cannot create '{model_name}'. Error: {e}"
                
                record = Model.create(values)
                res = {'id': record.id}
                if 'display_name' in Model._fields:
                    res['display_name'] = record.display_name
                return json.dumps(res, default=str)
            except Exception as e:
                return f"Error creating record: {e}"

        @tool
        def update_odoo_records(model_name: str, domain: list, values: dict):
            """
            Update existing records in an Odoo model.
            domain: list of tuples to find records to update (e.g., [["id", "=", 123]])
            values: dictionary of field values to update.
            """
            try:
                Model = env.get(model_name)
                if Model is None:
                    return f"Model {model_name} not found."
                
                try:
                    if hasattr(Model, 'check_access'):
                        Model.check_access('write')
                    else:
                        Model.check_access_rights('write')
                except Exception as e:
                    return f"Access Denied: Cannot write '{model_name}'. Error: {e}"
                
                records = Model.search(domain)
                if not records:
                    return "No records found matching the domain."
                
                records.write(values)
                return f"Successfully updated {len(records)} records."
            except Exception as e:
                return f"Error updating records: {e}"

        @tool
        def update_odoo_record_translations(model_name: str, domain: list, field_name: str, translations: dict):
            """
            Update translations for a specific field on existing records in an Odoo model.
            domain: list of tuples to find records to update (e.g., [["id", "=", 123]])
            field_name: the name of the translated field (e.g., 'name', 'description')
            translations: dictionary mapping language codes to translated strings (e.g., {"fr_FR": "Bonjour", "es_ES": "Hola"})
            """
            try:
                Model = env.get(model_name)
                if Model is None:
                    return f"Model {model_name} not found."
                
                try:
                    if hasattr(Model, 'check_access'):
                        Model.check_access('write')
                    else:
                        Model.check_access_rights('write')
                except Exception as e:
                    return f"Access Denied: Cannot write '{model_name}'. Error: {e}"
                
                records = Model.search(domain)
                if not records:
                    return "No records found matching the domain."
                
                if not hasattr(records, 'update_field_translations'):
                    return "This Odoo version does not support update_field_translations directly."

                for record in records:
                    record.update_field_translations(field_name, translations)
                
                return f"Successfully updated translations for field '{field_name}' on {len(records)} records."
            except Exception as e:
                return f"Error updating translations: {e}"

        @tool
        def delete_odoo_records(model_name: str, domain: list):
            """
            Delete existing records from an Odoo model.
            domain: list of tuples to find records to delete.
            """
            try:
                Model = env.get(model_name)
                if Model is None:
                    return f"Model {model_name} not found."
                
                try:
                    if hasattr(Model, 'check_access'):
                        Model.check_access('unlink')
                    else:
                        Model.check_access_rights('unlink')
                except Exception as e:
                    return f"Access Denied: Cannot delete '{model_name}'. Error: {e}"
                
                records = Model.search(domain)
                if not records:
                    return "No records found matching the domain."
                
                count = len(records)
                records.unlink()
                return f"Successfully deleted {count} records."
            except Exception as e:
                return f"Error deleting records: {e}"

        tools = [get_model_schema, read_odoo_records, create_odoo_record, update_odoo_records, update_odoo_record_translations, delete_odoo_records]

        # Configure LLM
        get_param = env['ir.config_parameter'].sudo().get_param
        provider = get_param('odoo_ai_chatbot.ai_provider', 'ollama')

        if provider == 'bedrock':
            boto_client = boto3.client(
                service_name='bedrock-runtime',
                region_name=get_param('odoo_ai_chatbot.bedrock_region', 'us-east-1'),
                aws_access_key_id=get_param('odoo_ai_chatbot.bedrock_aws_access_key'),
                aws_secret_access_key=get_param('odoo_ai_chatbot.bedrock_aws_secret_key')
            )
            llm = ChatBedrockConverse(
                client=boto_client,
                model_id=get_param('odoo_ai_chatbot.bedrock_model', 'anthropic.claude-3-haiku-20240307-v1:0')
            )
        else:
            ollama_base_url = get_param('odoo_ai_chatbot.ollama_base_url', 'http://localhost:11434')
            ollama_api_key = get_param('odoo_ai_chatbot.ollama_api_key', '')
            
            client_kwargs = {}
            if ollama_api_key:
                client_kwargs["headers"] = {
                    "Authorization": f"Bearer {ollama_api_key}",
                }
                
            llm = ChatOllama(
                base_url=ollama_base_url,
                model=get_param('odoo_ai_chatbot.ollama_model', 'llama3'),
                client_kwargs=client_kwargs,
                async_client_kwargs=client_kwargs,
            )

        return llm, tools
