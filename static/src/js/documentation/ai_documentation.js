/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class AiCeDocumentation extends Component {
    static template = "odoo_ai_ce.AiDocumentation";

    setup() {
        this.action = useService("action");
        this.notification = useService("notification");
        this.contentRef = useRef("contentBody");

        this.state = useState({
            isLoading: true,
            topics: [],
            categories: {},
            activeDocId: "index",
            activeTopic: null,
            content: "",
            headings: [],
            searchQuery: "",
            copiedAnchor: null,
            isCopiedAll: false,
        });

        onWillStart(async () => {
            await this.loadTopics();
            await this.loadContent(this.state.activeDocId);
        });
    }

    async loadTopics() {
        try {
            const data = await rpc("/ai_ce/documentation/topics", {});
            this.state.topics = data.topics || [];
            this.state.categories = data.categories || {};
        } catch (e) {
            console.error("Failed to load documentation topics:", e);
        }
    }

    async loadContent(docId) {
        this.state.isLoading = true;
        this.state.activeDocId = docId;
        try {
            const res = await rpc("/ai_ce/documentation/content", { doc_id: docId });
            this.state.activeTopic = res.topic;
            this.state.content = res.content || "";
            this.state.headings = res.headings || [];
        } catch (e) {
            console.error("Failed to load documentation content:", e);
            this.state.content = "# Error\nFailed to load content.";
        } finally {
            this.state.isLoading = false;
        }
    }

    get filteredTopics() {
        if (!this.state.searchQuery.trim()) {
            return this.state.topics;
        }
        const q = this.state.searchQuery.toLowerCase();
        return this.state.topics.filter(t => 
            t.title.toLowerCase().includes(q) || 
            t.description.toLowerCase().includes(q) ||
            t.category.toLowerCase().includes(q)
        );
    }

    get categoryGroups() {
        const groups = {};
        for (const topic of this.filteredTopics) {
            const cat = topic.category;
            if (!groups[cat]) {
                groups[cat] = [];
            }
            groups[cat].push(topic);
        }
        return groups;
    }

    onSelectTopic(docId) {
        if (this.state.activeDocId !== docId) {
            this.loadContent(docId);
            if (this.contentRef.el) {
                this.contentRef.el.scrollTop = 0;
            }
        }
    }

    scrollToHeading(anchorId) {
        if (!this.contentRef.el) return;
        const el = this.contentRef.el.querySelector(`[id="${anchorId}"]`);
        if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    }

    async copyMarkdown() {
        try {
            await navigator.clipboard.writeText(this.state.content);
            this.state.isCopiedAll = true;
            this.notification.add("Markdown guide copied to clipboard!", { type: "info" });
            setTimeout(() => {
                this.state.isCopiedAll = false;
            }, 2500);
        } catch (e) {
            this.notification.add("Could not copy markdown to clipboard.", { type: "warning" });
        }
    }

    async copyCode(codeText) {
        try {
            await navigator.clipboard.writeText(codeText);
            this.notification.add("Code snippet copied!", { type: "success" });
        } catch (e) {
            this.notification.add("Failed to copy code snippet.", { type: "warning" });
        }
    }

    openDashboard() {
        this.action.doAction("odoo_ai_ce.action_ai_ce_dashboard");
    }

    /**
     * Converts markdown text into structured, safe HTML with syntax highlighting,
     * alerts, tables, badge tags, and copy buttons.
     */
    get renderedHtml() {
        let md = this.state.content || "";

        // Escape HTML tags in raw text except intentional structures
        md = md.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

        // Code blocks: ```lang ... ```
        md = md.replace(/```([a-zA-Z0-9_\-\+]*)\n([\s\S]*?)```/g, (match, lang, code) => {
            const rawCode = code.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
            const escapedForAttr = encodeURIComponent(rawCode);
            return `
                <div class="o_ai_code_block position-relative my-3 rounded">
                    <div class="o_ai_code_header d-flex justify-content-between align-items-center px-3 py-1 bg-dark text-muted small border-bottom border-secondary">
                        <span class="font-monospace text-uppercase fw-bold">${lang || "text"}</span>
                        <button class="btn btn-sm btn-link text-light text-decoration-none copy-btn" onclick="navigator.clipboard.writeText(decodeURIComponent('${escapedForAttr}')).then(() => alert('Code copied to clipboard!'))">
                            <i class="fa fa-clone me-1"></i> Copy
                        </button>
                    </div>
                    <pre class="m-0 p-3 bg-dark text-light overflow-auto font-monospace small"><code>${code.trim()}</code></pre>
                </div>
            `;
        });

        // Inline code: `code`
        md = md.replace(/`([^`]+)`/g, '<code class="o_ai_inline_code px-1 py-0.5 rounded bg-light text-primary font-monospace small">$1</code>');

        // Alert blockquotes: > [!NOTE], > [!TIP], > [!WARNING], > [!IMPORTANT], > [!CAUTION]
        md = md.replace(/&gt;\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*\n((?:&gt;[^\n]*\n?)*)/gi, (match, type, body) => {
            const cleanBody = body.replace(/&gt;\s?/g, '').trim();
            const alertClass = {
                NOTE: 'alert-info',
                TIP: 'alert-success',
                IMPORTANT: 'alert-primary',
                WARNING: 'alert-warning',
                CAUTION: 'alert-danger'
            }[type.toUpperCase()] || 'alert-secondary';

            const iconClass = {
                NOTE: 'fa-info-circle',
                TIP: 'fa-lightbulb-o',
                IMPORTANT: 'fa-exclamation-circle',
                WARNING: 'fa-exclamation-triangle',
                CAUTION: 'fa-shield'
            }[type.toUpperCase()] || 'fa-info';

            return `
                <div class="alert ${alertClass} d-flex align-items-start my-3 shadow-sm rounded-3">
                    <i class="fa ${iconClass} fa-lg me-3 mt-1"></i>
                    <div>
                        <strong class="text-uppercase tracking-wider small d-block mb-1">${type}</strong>
                        <div>${cleanBody}</div>
                    </div>
                </div>
            `;
        });

        // Headings (# h1, ## h2, ### h3, #### h4)
        md = md.replace(/^#### (.*$)/gim, (match, text) => {
            const anchor = text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
            return `<h5 id="${anchor}" class="mt-4 mb-2 fw-bold text-secondary">${text}</h5>`;
        });
        md = md.replace(/^### (.*$)/gim, (match, text) => {
            const anchor = text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
            return `<h4 id="${anchor}" class="mt-4 mb-3 fw-bold text-dark border-bottom pb-1">${text}</h4>`;
        });
        md = md.replace(/^## (.*$)/gim, (match, text) => {
            const anchor = text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
            return `<h3 id="${anchor}" class="mt-5 mb-3 fw-bold text-primary border-bottom pb-2 d-flex align-items-center"><i class="fa fa-chevron-right small text-muted me-2"></i> ${text}</h3>`;
        });
        md = md.replace(/^# (.*$)/gim, (match, text) => {
            const anchor = text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
            return `<h2 id="${anchor}" class="mb-4 fw-bolder text-dark pb-2 border-bottom border-2">${text}</h2>`;
        });

        // Bold & Italic
        md = md.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        md = md.replace(/\*([^*]+)\*/g, '<em>$1</em>');

        // Horizontal Rules
        md = md.replace(/^---$/gim, '<hr class="my-4 text-muted opacity-25"/>');

        // Bullet lists
        md = md.replace(/^\s*-\s+(.*$)/gim, '<li class="mb-1">$1</li>');
        md = md.replace(/(<li class="mb-1">.*<\/li>\s*)+/g, '<ul class="ps-3 my-2">$0</ul>');

        // Tables
        md = md.replace(/(\|.+)+\|/g, (match) => {
            const rows = match.trim().split('\n');
            if (rows.length < 2) return match;
            let html = '<div class="table-responsive my-3"><table class="table table-hover table-bordered shadow-sm rounded overflow-hidden"><tbody>';
            rows.forEach((row, i) => {
                if (row.includes('---')) return; // separator row
                const cols = row.split('|').filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
                if (i === 0) {
                    html += '<thead class="table-light"><tr>';
                    cols.forEach(c => html += `<th class="px-3 py-2 text-uppercase small">${c.trim()}</th>`);
                    html += '</tr></thead><tbody>';
                } else {
                    html += '<tr>';
                    cols.forEach(c => html += `<td class="px-3 py-2 align-middle">${c.trim()}</td>`);
                    html += '</tr>';
                }
            });
            html += '</tbody></table></div>';
            return html;
        });

        // Paragraphs
        md = md.replace(/\n\n([^\n<]+)/g, '<p class="my-3 text-secondary lh-lg">$1</p>');

        return md;
    }
}

registry.category("actions").add("odoo_ai_ce_documentation", AiCeDocumentation);
