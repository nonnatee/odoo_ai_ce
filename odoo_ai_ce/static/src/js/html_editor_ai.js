/** @odoo-module **/

import { registry } from "@web/core/registry";

export const htmlEditorAiPlugin = {
    name: "html_editor_ai",
    setup(editor) {
        // Register powerbox slash command if powerbox available
        if (editor.plugins && editor.plugins.powerbox) {
            editor.plugins.powerbox.addCommand({
                category: "AI Tools",
                name: "AI Prompt / Draft",
                priority: 10,
                description: "Generate or improve text with AI Assistant",
                fontawesome: "fa-magic",
                callback: async () => {
                    const prompt = window.prompt("Enter AI instructions for drafting or improving text:");
                    if (!prompt) return;

                    try {
                        const env = odoo.__WOWL_DEBUG__.root.env;
                        const rpc = env.services.rpc;
                        const res = await rpc("/ai_ce/ask", { prompt: prompt });
                        if (res && res.answer) {
                            editor.insertText(res.answer);
                        }
                    } catch (e) {
                        console.error("AI powerbox error:", e);
                    }
                },
            });
        }
    },
};
