from odoo import http
from odoo.http import request

class AIChatbotController(http.Controller):

    @http.route('/ai_chatbot/send_message', type='jsonrpc', auth='user')
    def send_message(self, session_id, message):
        """
        Endpoint to send a message to the AI Chatbot.
        """
        response = request.env['ai.agent'].process_message(session_id, message)
        return response
    
    @http.route('/ai_chatbot/get_history', type='jsonrpc', auth='user')
    def get_history(self, session_id):
        if not session_id:
            return []
        session = request.env['ai.chat.session'].browse(session_id)
        if not session.exists():
            return []
        
        history = []
        for msg in session.message_ids:
            history.append({
                'role': msg.role,
                'content': msg.content
            })
        return history
