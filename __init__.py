"""
LoRA Backup Node for ComfyUI
============================
Copies all LoRAs that are ACTIVE in the current workflow (including
rgthree's Power Lora Loader: only enabled rows) to a target folder of
your choice - via a button directly on the node, without having to run
the workflow.

Installation:
  ComfyUI/custom_nodes/ComfyUI-LoRA-Backup/  <- this repository
  Then restart ComfyUI and reload the browser page (F5).

The node can be found under: Add Node -> utils -> LoRA Backup
"""

import os
import shutil

import folder_paths

WEB_DIRECTORY = "./web"

# File extensions that are treated as LoRA files
LORA_EXTENSIONS = (".safetensors", ".ckpt", ".pt", ".pth", ".bin")


def _collect_lora_names(prompt):
    """Scans the entire workflow (prompt JSON) for active LoRA file
    names. Disabled entries (e.g. Power Lora Loader rows with
    "on": false) are skipped."""
    found = set()
    if not prompt:
        return found

    known_loras = set(folder_paths.get_filename_list("loras"))

    def _is_disabled(d):
        if "on" in d and d["on"] in (False, "false", "False", 0):
            return True
        if "enabled" in d and d["enabled"] in (False, "false", "False", 0):
            return True
        if "switch" in d and str(d["switch"]).strip().lower() in ("off", "disable", "disabled", "false", "none"):
            return True
        return False

    def scan(value):
        if isinstance(value, str):
            v = value.strip()
            if v.lower().endswith(LORA_EXTENSIONS):
                v_norm = v.replace("\\", "/")
                for known in known_loras:
                    if known.replace("\\", "/") == v_norm:
                        found.add(known)
                        break
        elif isinstance(value, dict):
            if _is_disabled(value):
                return
            for sub in value.values():
                scan(sub)
        elif isinstance(value, (list, tuple)):
            for sub in value:
                scan(sub)

    for node in prompt.values():
        if isinstance(node, dict):
            scan(node.get("inputs", {}))

    return found


def _do_backup(prompt, target_folder, keep_subfolders=True,
               skip_existing=True):
    """Performs the actual copying and returns a report string."""
    loras = _collect_lora_names(prompt)
    if not loras:
        return "No active LoRAs found in the current workflow."

    target_folder = os.path.expanduser(str(target_folder).strip())
    if not target_folder:
        return "Error: No target folder specified."

    copied, skipped, errors = [], [], []

    for rel_name in sorted(loras):
        source = folder_paths.get_full_path("loras", rel_name)
        if source is None or not os.path.isfile(source):
            errors.append(f"{rel_name} (source file not found)")
            continue

        if keep_subfolders:
            target = os.path.join(target_folder, rel_name)
        else:
            target = os.path.join(target_folder, os.path.basename(rel_name))

        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)

            if skip_existing and os.path.isfile(target):
                if os.path.getsize(target) == os.path.getsize(source):
                    skipped.append(rel_name)
                    continue

            shutil.copy2(source, target)
            copied.append(rel_name)
            print(f"[LoRA Backup] Copied: {rel_name} -> {target}")

        except Exception as e:
            errors.append(f"{rel_name} ({e})")
            print(f"[LoRA Backup] ERROR for {rel_name}: {e}")

    parts = [f"{len(copied)} copied"]
    if skipped:
        parts.append(f"{len(skipped)} already present")
    if errors:
        parts.append(f"{len(errors)} errors")
    report = "LoRA Backup: " + ", ".join(parts)
    if copied:
        report += "\nCopied: " + ", ".join(copied)
    if errors:
        report += "\nErrors: " + "; ".join(errors)

    print(f"[LoRA Backup] {report}")
    return report


class LoraBackup:
    """Copies the workflow's active LoRAs to a target folder.
    Normally triggered via the button on the node; optionally also
    automatically on every run (auto_run = true)."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "target_folder": ("STRING", {
                    "default": "D:/LoRA_Favorites",
                    "multiline": False,
                }),
                "keep_subfolders": ("BOOLEAN", {"default": True}),
                "skip_existing": ("BOOLEAN", {"default": True}),
                # false = button only; true = additionally on every queue
                "auto_run": ("BOOLEAN", {"default": False,
                                         "label_on": "auto on every run",
                                         "label_off": "button only"}),
            },
            "optional": {
                "trigger": ("*", {}),
            },
            "hidden": {
                "prompt": "PROMPT",
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("report",)
    FUNCTION = "backup"
    OUTPUT_NODE = True
    CATEGORY = "utils"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def backup(self, target_folder, keep_subfolders, skip_existing,
               auto_run, prompt=None, trigger=None):
        if not auto_run:
            return ("LoRA Backup: auto mode off - copying via button only.",)
        report = _do_backup(prompt, target_folder,
                            keep_subfolders, skip_existing)
        return (report,)


# ---------------------------------------------------------------------------
# API endpoint for the button (called by the JavaScript on the node)
# ---------------------------------------------------------------------------
try:
    from server import PromptServer
    from aiohttp import web

    @PromptServer.instance.routes.post("/lora_backup/copy")
    async def lora_backup_copy(request):
        try:
            data = await request.json()
            report = _do_backup(
                data.get("prompt") or {},
                data.get("target_folder", ""),
                bool(data.get("keep_subfolders", True)),
                bool(data.get("skip_existing", True)),
            )
            return web.json_response({"ok": True, "report": report})
        except Exception as e:
            print(f"[LoRA Backup] API error: {e}")
            return web.json_response({"ok": False, "report": f"Error: {e}"},
                                     status=500)
except Exception as e:
    # Outside of ComfyUI (e.g. during testing) the server is not available
    print(f"[LoRA Backup] Note: button endpoint not registered ({e})")


NODE_CLASS_MAPPINGS = {
    "LoraBackup": LoraBackup,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoraBackup": "LoRA Backup (copy used LoRAs)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
