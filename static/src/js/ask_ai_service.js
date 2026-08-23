/** @odoo-module **/

import { registry } from "@web/core/registry";
import { AskAiModal } from "./ask_ai_modal";

export const askAiService = {
    dependencies: ["dialog", "orm"],
    start(env, { dialog, orm }) {
        function openAskAi(recordContext = {}) {
            dialog.add(AskAiModal, {
                recordContext: recordContext,
            });
        }

        // Global hotkey listener (Ctrl+K / Cmd+K)
        window.addEventListener("keydown", (ev) => {
            if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === "k") {
                // If not typing in input/textarea, open Ask AI
                const tag = ev.target ? ev.target.tagName : "";
                if (tag !== "INPUT" && tag !== "TEXTAREA") {
                    ev.preventDefault();
                    openAskAi();
                }
            }
        });

        return {
            open: openAskAi,
        };
    },
};

registry.category("services").add("ask_ai_service", askAiService);
