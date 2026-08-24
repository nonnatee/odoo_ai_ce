/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class AiCeDashboard extends Component {
    static template = "odoo_ai_ce.AiDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            providerCount: 0,
            activeProviders: 0,
            modelCount: 0,
            toolCount: 0,
            pendingConsents: 0,
            totalLogs: 0,
            hermesStatus: {
                is_running: false,
                version: "-",
                process_pid: 0,
                memory_mb: 0,
                cpu_percent: 0,
                active_acp_sessions: 0
            },
            providersList: [],
            recentLogs: [],
            isLoading: true,
            isControlling: false,
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        this.state.isLoading = true;
        try {
            const [providers, models, tools, consents, logs, hermes] = await Promise.all([
                this.orm.searchRead("ai_ce.provider", [], ["name", "service", "connection_status", "priority", "active"]),
                this.orm.searchCount("ai_ce.model", []),
                this.orm.searchCount("ai_ce.tool", [("active", "=", true)]),
                this.orm.searchCount("ai_ce.consent", [("state", "=", "pending")]),
                this.orm.searchCount("ai_ce.log", []),
                rpc("/ai_ce/hermes/status", {}).catch(() => ({ is_running: false })),
            ]);

            this.state.providerCount = providers.length;
            this.state.activeProviders = providers.filter(p => p.active && p.connection_status === 'connected').length;
            this.state.providersList = providers;
            this.state.modelCount = models;
            this.state.toolCount = tools;
            this.state.pendingConsents = consents;
            this.state.totalLogs = logs;
            this.state.hermesStatus = hermes;

            // Load recent audit logs
            this.state.recentLogs = await this.orm.searchRead("ai_ce.log", [], ["timestamp", "user_id", "client_type", "model_used", "execution_time_ms", "status"], {
                limit: 8,
                order: "id desc"
            });
        } catch (e) {
            console.error("Failed to load AI Dashboard data:", e);
        } finally {
            this.state.isLoading = false;
        }
    }

    async controlSupervisor(action) {
        this.state.isControlling = true;
        try {
            const res = await rpc("/ai_ce/hermes/supervisor/control", { action: action });
            if (res.error) {
                this.notification.add(res.error, { type: "danger" });
            } else {
                this.state.hermesStatus = res;
                this.notification.add(`Hermes Daemon action '${action}' completed.`, { type: "success" });
            }
        } catch (e) {
            this.notification.add(`Failed to execute '${action}': ${e.message || e}`, { type: "danger" });
        } finally {
            this.state.isControlling = false;
            await this.loadDashboardData();
        }
    }

    openAction(actionName) {
        this.action.doAction(actionName);
    }
}

registry.category("actions").add("odoo_ai_ce_dashboard", AiCeDashboard);
