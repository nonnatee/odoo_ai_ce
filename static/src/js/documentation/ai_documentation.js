/** @odoo-module **/

import { Component, useState, onWillStart, useRef, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

function slugify(text) {
    return (text || "")
        .toLowerCase()
        .replace(/<[^>]*>/g, "")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)/g, "");
}

function parseMarkdown(rawMd) {
    if (!rawMd) return "";

    // 1. Extract and protect code blocks
    const codeBlocks = [];
    let text = rawMd.replace(/```([a-zA-Z0-9_\-\+]*)\r?\n([\s\S]*?)```/g, (match, lang, code) => {
        const index = codeBlocks.length;
        codeBlocks.push({ lang: lang.trim() || "text", code: code.trimEnd() });
        return `@@CODE_BLOCK_${index}@@`;
    });

    // 2. Extract and protect inline code
    const inlineCodes = [];
    text = text.replace(/`([^`\n]+)`/g, (match, code) => {
        const index = inlineCodes.length;
        inlineCodes.push(code);
        return `@@INLINE_CODE_${index}@@`;
    });

    // 3. Escape HTML characters in remaining text
    text = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // 4. Alerts & Callouts: > [!NOTE], > [!TIP], > [!IMPORTANT], > [!WARNING], > [!CAUTION]
    text = text.replace(/^(&gt;|>)\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\r?\n((?:(?:&gt;|>)[^\n]*\r?\n?)*)/gim, (match, gt, type, body) => {
        const cleanBody = body.replace(/^(?:&gt;|>)\s?/gm, "").trim();
        const upperType = type.toUpperCase();
        const alertConfig = {
            NOTE: { cls: "alert-info", icon: "fa-info-circle" },
            TIP: { cls: "alert-success", icon: "fa-lightbulb-o" },
            IMPORTANT: { cls: "alert-primary", icon: "fa-exclamation-circle" },
            WARNING: { cls: "alert-warning", icon: "fa-exclamation-triangle" },
            CAUTION: { cls: "alert-danger", icon: "fa-shield" },
        }[upperType] || { cls: "alert-secondary", icon: "fa-info" };

        return `<div class="alert ${alertConfig.cls} d-flex align-items-start my-3 shadow-sm rounded-3">
            <i class="fa ${alertConfig.icon} fa-lg me-3 mt-1 flex-shrink-0"></i>
            <div class="flex-grow-1">
                <strong class="text-uppercase small d-block mb-1">${upperType}</strong>
                <div>${cleanBody}</div>
            </div>
        </div>\n\n`;
    });

    // 5. Standard Blockquotes
    text = text.replace(/^((?:(?:&gt;|>)[^\n]*\r?\n?)+)/gm, (match) => {
        const quoteContent = match.replace(/^(?:&gt;|>)\s?/gm, "").trim();
        return `<blockquote class="blockquote ps-3 border-start border-3 border-primary my-3 text-muted fst-italic">${quoteContent}</blockquote>\n\n`;
    });

    // 6. Tables
    text = text.replace(/((?:^\|[^\n]+\|\r?\n)+)/gm, (tableBlock) => {
        const lines = tableBlock.trim().split("\n").map(l => l.trim()).filter(Boolean);
        if (lines.length < 2) return tableBlock;

        let html = '<div class="table-responsive my-3"><table class="table table-hover table-bordered shadow-sm rounded overflow-hidden"><tbody>';
        let isHeader = true;

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            if (/^\|[\s\-:|]+\|$/.test(line)) {
                isHeader = false;
                continue;
            }
            const cells = line.split("|").slice(1, -1);
            if (isHeader && i === 0) {
                html += '<thead class="table-light"><tr>';
                cells.forEach(c => {
                    html += `<th class="px-3 py-2 text-uppercase small fw-bold">${c.trim()}</th>`;
                });
                html += "</tr></thead><tbody>";
                isHeader = false;
            } else {
                html += "<tr>";
                cells.forEach(c => {
                    html += `<td class="px-3 py-2 align-middle">${c.trim()}</td>`;
                });
                html += "</tr>";
            }
        }
        html += "</tbody></table></div>\n\n";
        return html;
    });

    // 7. Headings (# h1, ## h2, ### h3, #### h4)
    text = text.replace(/^####\s+(.+)$/gm, (m, title) => {
        const slug = slugify(title);
        return `<h5 id="${slug}" class="mt-4 mb-2 fw-bold text-secondary">${title}</h5>`;
    });
    text = text.replace(/^###\s+(.+)$/gm, (m, title) => {
        const slug = slugify(title);
        return `<h4 id="${slug}" class="mt-4 mb-3 fw-bold text-dark border-bottom pb-1">${title}</h4>`;
    });
    text = text.replace(/^##\s+(.+)$/gm, (m, title) => {
        const slug = slugify(title);
        return `<h3 id="${slug}" class="mt-5 mb-3 fw-bold text-primary border-bottom pb-2 d-flex align-items-center"><i class="fa fa-chevron-right small text-muted me-2"></i> ${title}</h3>`;
    });
    text = text.replace(/^#\s+(.+)$/gm, (m, title) => {
        const slug = slugify(title);
        return `<h2 id="${slug}" class="mb-4 fw-bolder text-dark pb-2 border-bottom border-2">${title}</h2>`;
    });

    // 8. Horizontal Rules
    text = text.replace(/^(?:---|___|\*\*\*)$/gm, '<hr class="my-4 text-muted opacity-25"/>');

    // 9. Links: [Label](url)
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, label, url) => {
        const cleanUrl = url.trim();
        const docMatch = cleanUrl.match(/^(?:doc\/)?([a-zA-Z0-9_-]+)\.md(?:#([a-zA-Z0-9_-]+))?$/);
        if (docMatch) {
            const targetDocId = docMatch[1];
            const targetAnchor = docMatch[2] || "";
            return `<a href="#" class="o_ai_doc_link text-decoration-none fw-semibold text-primary" data-doc-id="${targetDocId}" data-anchor="${targetAnchor}"><i class="fa fa-file-text-o me-1"></i>${label}</a>`;
        }
        if (cleanUrl.startsWith("#")) {
            return `<a href="${cleanUrl}" class="o_ai_anchor_link text-decoration-none fw-semibold text-primary">${label}</a>`;
        }
        return `<a href="${cleanUrl}" target="_blank" rel="noopener noreferrer" class="text-decoration-none fw-semibold text-primary">${label} <i class="fa fa-external-link small opacity-75"></i></a>`;
    });

    // 10. Bold, Italic, Strikethrough
    text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    text = text.replace(/__([^_]+)__/g, "<strong>$1</strong>");
    text = text.replace(/(^|[^\*])\*([^*\n]+)\*([^\*]|$)/g, "$1<em>$2</em>$3");
    text = text.replace(/(^|[^_])_([^_\n]+)_([^_]|$)/g, "$1<em>$2</em>$3");
    text = text.replace(/~~([^~]+)~~/g, "<del>$1</del>");

    // 11. Lists (Ordered and Unordered)
    text = text.replace(/^(\s*)[-\*]\s+(.+)$/gm, (match, indent, item) => {
        const depth = Math.floor(indent.length / 2);
        return `<li class="o_ai_li depth-${depth} mb-1">${item}</li>`;
    });
    text = text.replace(/^(\s*)\d+\.\s+(.+)$/gm, (match, indent, item) => {
        const depth = Math.floor(indent.length / 2);
        return `<li class="o_ai_oli depth-${depth} mb-1">${item}</li>`;
    });

    text = text.replace(/((?:<li class="o_ai_li[^"]*">.*?<\/li>\s*)+)/gs, '<ul class="o_ai_list ps-4 my-2">$1</ul>');
    text = text.replace(/((?:<li class="o_ai_oli[^"]*">.*?<\/li>\s*)+)/gs, '<ol class="o_ai_olist ps-4 my-2">$1</ol>');

    // 12. Paragraphs
    const blocks = text.split(/\n\s*\n/);
    const formattedBlocks = blocks.map(block => {
        const trimmed = block.trim();
        if (!trimmed) return "";
        if (/^<(h[1-6]|div|table|ul|ol|blockquote|hr|pre)/i.test(trimmed)) {
            return trimmed;
        }
        if (trimmed.startsWith("@@CODE_BLOCK_")) {
            return trimmed;
        }
        return `<p class="my-3 text-secondary lh-lg">${trimmed.replace(/\n/g, "<br/>")}</p>`;
    });
    text = formattedBlocks.join("\n\n");

    // 13. Restore Inline Code
    text = text.replace(/@@INLINE_CODE_(\d+)@@/g, (m, idx) => {
        const rawCode = inlineCodes[parseInt(idx, 10)] || "";
        const escaped = rawCode.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        return `<code class="o_ai_inline_code px-1 py-0.5 rounded bg-light text-primary font-monospace small">${escaped}</code>`;
    });

    // 14. Restore Code Blocks with Copy Buttons
    text = text.replace(/@@CODE_BLOCK_(\d+)@@/g, (m, idx) => {
        const item = codeBlocks[parseInt(idx, 10)];
        if (!item) return "";
        const lang = item.lang || "text";
        const rawCode = item.code;
        const escaped = rawCode.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

        return `
            <div class="o_ai_code_block position-relative my-3 rounded-3 overflow-hidden shadow-sm">
                <div class="o_ai_code_header d-flex justify-content-between align-items-center px-3 py-1 bg-dark text-muted small border-bottom border-secondary border-opacity-25">
                    <span class="font-monospace text-uppercase fw-bold"><i class="fa fa-code me-1 text-primary"></i> ${lang}</span>
                    <button type="button" class="btn btn-sm btn-link text-light text-decoration-none o_ai_copy_snippet_btn py-0 px-2">
                        <i class="fa fa-clone me-1"></i> Copy
                    </button>
                </div>
                <pre class="m-0 p-3 bg-dark text-light overflow-auto font-monospace small"><code>${escaped}</code></pre>
            </div>
        `;
    });

    return text;
}

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

    onSelectTopic(docId, anchor = null) {
        if (this.state.activeDocId !== docId) {
            this.loadContent(docId).then(() => {
                if (anchor) {
                    setTimeout(() => this.scrollToHeading(anchor), 100);
                } else if (this.contentRef.el) {
                    this.contentRef.el.scrollTop = 0;
                }
            });
        } else if (anchor) {
            this.scrollToHeading(anchor);
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

    onMarkdownBodyClick(ev) {
        // Handle code block copy button
        const copyBtn = ev.target.closest(".o_ai_copy_snippet_btn");
        if (copyBtn) {
            ev.preventDefault();
            const codeBlock = copyBtn.closest(".o_ai_code_block");
            const codeEl = codeBlock ? codeBlock.querySelector("pre code") : null;
            if (codeEl) {
                const codeText = codeEl.innerText;
                navigator.clipboard.writeText(codeText).then(() => {
                    const originalHtml = copyBtn.innerHTML;
                    copyBtn.innerHTML = '<i class="fa fa-check text-success me-1"></i> Copied!';
                    this.notification.add("Code snippet copied to clipboard!", { type: "success" });
                    setTimeout(() => {
                        copyBtn.innerHTML = originalHtml;
                    }, 2000);
                });
            }
            return;
        }

        // Handle internal doc link click
        const docLink = ev.target.closest(".o_ai_doc_link");
        if (docLink) {
            ev.preventDefault();
            const docId = docLink.dataset.docId;
            const anchor = docLink.dataset.anchor;
            if (docId) {
                this.onSelectTopic(docId, anchor);
            }
            return;
        }

        // Handle anchor link click
        const anchorLink = ev.target.closest(".o_ai_anchor_link");
        if (anchorLink) {
            ev.preventDefault();
            const href = anchorLink.getAttribute("href") || "";
            const anchorId = href.replace(/^#/, "");
            if (anchorId) {
                this.scrollToHeading(anchorId);
            }
        }
    }

    openDashboard() {
        this.action.doAction("odoo_ai_ce.action_ai_ce_dashboard");
    }

    get renderedHtml() {
        return markup(parseMarkdown(this.state.content));
    }
}

registry.category("actions").add("odoo_ai_ce_documentation", AiCeDocumentation);
