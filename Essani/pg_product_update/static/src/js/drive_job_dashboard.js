/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onWillUnmount, useState } from "@odoo/owl";

export class PgProductUpdateDriveJobDashboard extends Component {
    static template = "pg_product_update.DriveJobDashboard";
    static props = ["action", "*"];

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({
            loading: true,
            error: "",
            job: null,
            lastRefresh: "",
        });
        this.jobId = this.props.action.params.job_id;
        this.pollHandle = null;
        this.isLoadingJob = false;
        this.jobFields = [
            "name",
            "state",
            "phase",
            "discovery_done",
            "discovered_count",
            "unaccounted_count",
            "progress_percent",
            "processed_count",
            "skipped_count",
            "pending_count",
            "scan_remaining_count",
            "total_count",
            "error_count",
            "current_item_display",
            "current_item_attempts",
            "duration_seconds",
            "started_at",
            "finished_at",
            "last_error",
            "skipped_items_preview",
            "unaccounted_items_preview",
            "trace_events_preview",
        ];

        onWillStart(async () => {
            await this.loadJob();
            this.startPolling();
        });

        onWillUnmount(() => this.stopPolling());
    }

    startPolling() {
        this.stopPolling();
        this.pollHandle = setInterval(() => this.loadJob(), 3000);
    }

    stopPolling() {
        if (this.pollHandle) {
            clearInterval(this.pollHandle);
            this.pollHandle = null;
        }
    }

    async loadJob() {
        if (this.isLoadingJob) {
            return;
        }
        this.isLoadingJob = true;
        try {
            const [job] = await this.orm.searchRead(
                "product.update.drive.job",
                [["id", "=", this.jobId]],
                this.jobFields,
                { limit: 1 }
            );
            this.state.job = job || null;
            this.state.error = job ? "" : "Import job not found.";
            this.state.loading = false;
            this.state.lastRefresh = new Date().toLocaleTimeString();
            if (job && job.state !== "running") {
                this.stopPolling();
            }
        } catch (error) {
            this.state.error = error.message || "Unable to load import progress.";
            this.state.loading = false;
        } finally {
            this.isLoadingJob = false;
        }
    }

    async refreshNow() {
        await this.loadJob();
    }

    async forceStartImport() {
        const action = await this.orm.call("product.update.drive.job", "action_force_start_processing", [[this.jobId]]);
        if (action) {
            await this.actionService.doAction(action);
            return;
        }
        await this.loadJob();
    }

    async openJobForm() {
        await this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "product.update.drive.job",
            res_id: this.jobId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    async openJobList() {
        await this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Import Jobs",
            res_model: "product.update.drive.job",
            views: [
                [false, "list"],
                [false, "form"],
            ],
            target: "current",
        });
    }

    get progressStyle() {
        const value = this.state.job?.progress_percent || 0;
        return `width: ${value}%;`;
    }

    get progressBarClass() {
        const state = this.state.job?.state;
        if (state === "done") {
            return "bg-success";
        }
        if (state === "failed") {
            return "bg-danger";
        }
        return "progress-bar-striped progress-bar-animated";
    }

    get progressLabel() {
        const value = this.state.job?.progress_percent || 0;
        return `${value.toFixed(1)}%`;
    }

    get progressTitle() {
        return this.state.job?.discovery_done ? "Overall Progress" : "Estimated Progress";
    }

    get totalCountLabel() {
        return this.state.job?.discovery_done ? "Total Products" : "Estimated Total";
    }

    get progressSummary() {
        const job = this.state.job;
        if (!job) {
            return "";
        }
        if (job.discovery_done) {
            return `${job.processed_count} processed, ${job.skipped_count || 0} skipped, ${job.unaccounted_count || 0} unaccounted, ${job.total_count} discovered`;
        }
        return `${job.processed_count} processed, ${job.skipped_count || 0} skipped, ${job.unaccounted_count || 0} unaccounted, ${job.discovered_count} discovered so far`;
    }

    get durationLabel() {
        const totalSeconds = this.state.job?.duration_seconds || 0;
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        if (hours) {
            return `${hours}h ${minutes}m ${seconds}s`;
        }
        if (minutes) {
            return `${minutes}m ${seconds}s`;
        }
        return `${seconds}s`;
    }

    get phaseLabel() {
        const labels = {
            discovery: "Discovering folders",
            processing: "Updating products",
            done: "Completed",
            failed: "Failed",
        };
        return labels[this.state.job?.phase] || "Running";
    }

    get isForceStartAvailable() {
        return this.state.job?.state === "running" && this.state.job?.phase === "discovery";
    }
}

registry.category("actions").add(
    "pg_product_update.drive_job_dashboard",
    PgProductUpdateDriveJobDashboard
);
