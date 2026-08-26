/** @odoo-module **/

import { registry } from "@web/core/registry";
import { AskAiModal } from "./ask_ai_modal";

export const askAiService = {
    dependencies: ["dialog", "orm"],
    start(env, { dialog, orm }) {
        function extractActiveContext(explicitContext = {}) {
            const context = {
                url: window.location.pathname,
                href: window.location.href,
                page_title: document.title,
                ...explicitContext,
            };

            const pageMeta = document.querySelector('meta[name="page_id"]');
            if (pageMeta && !context.page_id) {
                context.page_id = parseInt(pageMeta.content);
            }

            return context;
        }

        function openAskAi(recordContext = {}) {
            dialog.add(AskAiModal, {
                recordContext: extractActiveContext(recordContext),
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
