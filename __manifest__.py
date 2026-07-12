{
    'name': 'AI Chatbot (LangChain/LangGraph)',
    'version': '1.5',
    'category': 'Productivity',
    'summary': 'AI Chatbot powered by LangChain and LangGraph for Odoo.',
    'description': """
        AI Chatbot that answers questions from your current database and modules.
        Supports Amazon Bedrock, Ollama, and more via LangChain.
    """,
    'author': 'Tarang Kushwaha',
    'website': 'https://tarang7651.github.io/',
    'external_dependencies': {
        'python': ['langchain', 'langchain-community', 'langchain-aws', 'langgraph'],
    },
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/res_config_settings_views.xml',
        'views/ai_chat_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_ai_chatbot/static/src/components/chatbot/*.js',
            'odoo_ai_chatbot/static/src/components/chatbot/*.xml',
            'odoo_ai_chatbot/static/src/components/chatbot/*.scss',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
