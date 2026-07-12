from odoo import models, fields, api

PENDING_ACTION_TTL_MINUTES = 10


class AIPendingAction(models.Model):
    _name = 'ai.pending.action'
    _description = 'AI Agent action awaiting explicit user confirmation'
    _order = 'create_date desc'

    session_id = fields.Many2one('ai.chat.session', required=True, ondelete='cascade', index=True)
    user_id = fields.Many2one('res.users', required=True, default=lambda self: self.env.user, index=True)

    action_type = fields.Selection([
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('translate', 'Update Translations'),
    ], required=True)

    model_name = fields.Char(required=True)
    domain = fields.Char(required=True, help="JSON-encoded search domain")
    values = fields.Char(help="JSON-encoded write values (update only)")
    field_name = fields.Char(help="Translated field name (translate only)")
    translations = fields.Char(help="JSON-encoded lang->value map (translate only)")

    record_count = fields.Integer(help="Number of matching records at proposal time")
    state = fields.Selection([
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ], default='pending', required=True, index=True)

    @api.model
    def _expire_stale(self):
        """Mark pending actions older than the TTL as expired. Call this
        before creating/confirming actions, or via a cron."""
        cutoff = fields.Datetime.now() - fields.Datetime.to_timedelta(f"{PENDING_ACTION_TTL_MINUTES} minutes") \
            if hasattr(fields.Datetime, 'to_timedelta') else None
        # Simpler, dependency-free cutoff calculation:
        from datetime import timedelta
        cutoff = fields.Datetime.now() - timedelta(minutes=PENDING_ACTION_TTL_MINUTES)
        stale = self.search([('state', '=', 'pending'), ('create_date', '<', cutoff)])
        stale.write({'state': 'expired'})
        return stale

    def is_expired(self):
        self.ensure_one()
        from datetime import timedelta
        return fields.Datetime.now() - self.create_date > timedelta(minutes=PENDING_ACTION_TTL_MINUTES)