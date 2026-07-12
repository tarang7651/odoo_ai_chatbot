from odoo import models, fields, api

class AIChatSession(models.Model):
    _name = 'ai.chat.session'
    _description = 'AI Chat Session'
    _order = 'create_date desc'

    name = fields.Char(string="Session Name", compute="_compute_name", store=True)
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.uid)
    message_ids = fields.One2many('ai.chat.message', 'session_id', string="Messages")
    summary = fields.Text(string="Conversation Summary", default="")

    @api.depends('create_date')
    def _compute_name(self):
        for record in self:
            record.name = f"Chat Session - {record.create_date}"

    @api.model
    def get_current_session(self):
        chat_color = self.env['ir.config_parameter'].sudo().get_param('odoo_ai_chatbot.ai_chat_color', '#714B67')
        session = self.search([('user_id', '=', self.env.uid)], limit=1, order='create_date desc')
        
        if session:
            messages = []
            for msg in session.message_ids.sorted('create_date'):
                messages.append({
                    'role': msg.role,
                    'content': msg.content
                })
            return {
                'session_id': session.id,
                'messages': messages,
                'chat_color': chat_color
            }
        return {
            'session_id': False,
            'messages': [],
            'chat_color': chat_color
        }

class AIChatMessage(models.Model):
    _name = 'ai.chat.message'
    _description = 'AI Chat Message'
    _order = 'create_date asc'

    session_id = fields.Many2one('ai.chat.session', string="Session", required=True, ondelete='cascade')
    role = fields.Selection([
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System')
    ], string="Role", required=True)
    content = fields.Html(string="Content", required=True)
    is_summarized = fields.Boolean(string="Is Summarized", default=False)
