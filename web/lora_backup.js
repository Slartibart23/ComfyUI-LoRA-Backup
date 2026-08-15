// LoRA Backup - adds a "Copy now" button to the node.
// The button reads the current workflow from the browser and sends it
// to the server, which copies the active LoRAs to the target folder.
// File location: ComfyUI/custom_nodes/ComfyUI-LoRA-Backup/web/lora_backup.js

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

function showMessage(text, isError = false) {
    // New frontend: nice toast; old frontend: simple alert
    const toast = app.extensionManager?.toast;
    if (toast?.add) {
        toast.add({
            severity: isError ? "error" : "success",
            summary: "LoRA Backup",
            detail: text,
            life: 8000,
        });
    } else {
        alert("LoRA Backup\n\n" + text);
    }
}

app.registerExtension({
    name: "lora_backup.copy_button",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "LoraBackup") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);

            const node = this;
            const button = node.addWidget("button", "📂 Copy now", null, async () => {
                try {
                    button.name = "⏳ Copying ...";
                    node.setDirtyCanvas(true, false);

                    // Convert the current workflow to the API prompt format
                    // (muted/bypassed nodes are automatically excluded)
                    const p = await app.graphToPrompt();

                    const getVal = (name) =>
                        node.widgets?.find((w) => w.name === name)?.value;

                    const res = await api.fetchApi("/lora_backup/copy", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            prompt: p.output,
                            target_folder: getVal("target_folder"),
                            keep_subfolders: getVal("keep_subfolders"),
                            skip_existing: getVal("skip_existing"),
                        }),
                    });

                    const data = await res.json();
                    showMessage(data.report ?? "Unknown response from server.", !data.ok);
                } catch (err) {
                    console.error("[LoRA Backup]", err);
                    showMessage("Error while copying: " + err, true);
                } finally {
                    button.name = "📂 Copy now";
                    node.setDirtyCanvas(true, false);
                }
            });
            // Do not save the button in the workflow JSON
            button.serialize = false;
        };
    },
});
