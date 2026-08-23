/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class AskAiModal extends Component {
    static template = "odoo_ai_ce.AskAiModal";
    static components = { Dialog };
    static props = {
        close: { type: Function },
        recordContext: { type: Object, optional: true },
    };

    setup() {
        this.notification = useService("notification");
        this.state = useState({
            inputPrompt: "",
            isLoading: false,
            sessionId: null,
            messages: [
                {
                    role: "assistant",
                    content: "Hello! I am your Odoo AI Assistant. Ask me to query database records, summarize documents, calculate pricing, or draft responses.",
                }
            ],
        });
    }

    async sendMessage() {
        const prompt = this.state.inputPrompt.trim();
        if (!prompt || this.state.isLoading) return;

        this.state.messages.push({ role: "user", content: prompt });
        this.state.inputPrompt = "";
        this.state.isLoading = true;

        try {
            const response = await rpc("/ai_ce/ask", {
                prompt: prompt,
                session_id: this.state.sessionId,
                record_context: this.props.recordContext || {},
            });

            if (response.error) {
                this.state.messages.push({
                    role: "assistant",
                    content: `❌ Error: ${response.error}`,
                });
            } else {
                this.state.sessionId = response.session_id;
                this.state.messages.push({
                    role: "assistant",
                    content: response.answer || "No response received.",
                });
            }
        } catch (err) {
            this.state.messages.push({
                role: "assistant",
                content: `❌ Connection Error: ${err.message || err}`,
            });
        } finally {
            this.state.isLoading = false;
        }
    }

    onKeyDown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendMessage();
        }
    }

    copyMessage(content) {
        navigator.clipboard.writeText(content);
        this.notification.add("Copied to clipboard!", { type: "info" });
    }
}
