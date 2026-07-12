/** @odoo-module **/

import { Component, useState, onWillStart, useRef, useEffect, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

export class AIChatbot extends Component {
    setup() {
        this.orm = useService("orm");
        this.messagesContainerRef = useRef("messagesContainer");
        this.state = useState({
            messages: [],
            inputValue: "",
            isLoading: false,
            sessionId: null,
            isOpen: false,
            isHovered: false,
            isMaximized: false,
            chatColor: "#714B67"
        });

        onWillStart(async () => {
            try {
                const latestSession = await this.orm.call("ai.chat.session", "get_current_session", []);
                if (latestSession) {
                    this.state.chatColor = latestSession.chat_color || "#714B67";
                    if (latestSession.session_id) {
                        this.state.sessionId = latestSession.session_id;
                        if (latestSession.messages && latestSession.messages.length > 0) {
                            this.state.messages = latestSession.messages.map(msg => ({
                                role: msg.role,
                                content: markup(msg.content)
                            }));
                        }
                    }
                }
            } catch (e) {
                console.warn("Failed to load previous session:", e);
            }
        });

        useEffect(() => {
            if (this.messagesContainerRef.el) {
                this.messagesContainerRef.el.scrollTop = this.messagesContainerRef.el.scrollHeight;
            }
        }, () => [this.state.messages.length, this.state.isOpen]);
    }

    async toggleChat() {
        this.state.isOpen = !this.state.isOpen;
        if (this.state.isOpen) {
            if (!this.state.sessionId) {
                await this.startNewChat();
            } else if (this.state.messages.length === 0) {
                this.state.messages = [{
                    role: "assistant",
                    content: markup("Hello! I'm your AI assistant. ✨<br/>I can help you query Odoo data and list modules. How can I assist you today?")
                }];
            }
        }
    }
    
    closeChat() {
        this.state.isOpen = false;
    }

    toggleMaximize() {
        this.state.isMaximized = !this.state.isMaximized;
    }

    async startNewChat() {
        try {
            const sessionId = await this.orm.create("ai.chat.session", [{}]);
            this.state.sessionId = sessionId[0];
            this.state.messages = [{
                role: "assistant",
                content: markup("Hello! I'm your AI assistant. ✨<br/>I can help you query Odoo data and list modules. How can I assist you today?")
            }];
        } catch (e) {
            console.error("Failed to create new chat session:", e);
        }
    }

    async sendMessage() {
        if (!this.state.inputValue.trim() || this.state.isLoading) return;
        
        const userMessage = this.state.inputValue;
        this.state.messages.push({ role: "user", content: markup(userMessage) });
        this.state.inputValue = "";
        this.state.isLoading = true;

        try {
            const response = await this.orm.call("ai.agent", "process_message", [
                this.state.sessionId,
                userMessage,
            ]);
            this.state.messages.push({ role: "assistant", content: markup(response.response) });
        } catch (error) {
            console.error("Chatbot Error:", error);
            this.state.messages.push({ role: "assistant", content: markup("Oops! I encountered an error. Please try again later.") });
        } finally {
            this.state.isLoading = false;
        }
    }

    onInputKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendMessage();
        }
    }
}

AIChatbot.template = "odoo_ai_chatbot.SystrayItem";

export const systrayItem = {
    Component: AIChatbot,
};

registry.category("systray").add("odoo_ai_chatbot.AIChatbot", systrayItem, { sequence: 100 });
