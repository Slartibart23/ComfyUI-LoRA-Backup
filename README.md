# ComfyUI-LoRA-Backup

**Copy the LoRAs that are actually active in your current workflow to any folder — with one click.**

## Why this node exists

Sometimes a combination of LoRAs just works *exceptionally* well together. When that happens, you often want to use exactly these LoRAs in another ComfyUI installation — on a second machine, a portable setup, or a fresh install. Manually hunting down which LoRA files were active in the workflow, finding them in your (usually huge) `models/loras` folder and copying them over is tedious and error-prone.

This node solves that: press one button and all LoRAs that are **currently active** in your workflow are copied to a target folder of your choice (e.g. on another drive or a network share). From there you can move them to any other ComfyUI installation.

## Features

- **One-click copy** — a "📂 Copy now" button directly on the node, no need to run the workflow
- **Only active LoRAs** — disabled rows in rgthree's **Power Lora Loader** (`on: false`) are skipped, as are muted/bypassed nodes
- **Works with all common loaders** — LoraLoader, LoraLoaderModelOnly, Power Lora Loader, LoRA stackers, etc. The node scans the workflow for LoRA *file names*, not for specific node types
- **Keeps your folder structure** — subfolders from your `loras` directory are recreated in the target folder (optional)
- **Skips existing files** — already copied LoRAs (same size) are not copied again (optional)
- **Optional auto mode** — if you want, the node can also copy automatically on every queue

## Installation

1. Open a terminal in `ComfyUI/custom_nodes/`
2. Clone this repository:

   ```
   git clone https://github.com/Slartibart23/ComfyUI-LoRA-Backup.git
   ```

   Or download the repository as a ZIP and extract it into `custom_nodes/` so that the structure looks like this:

   ```
   ComfyUI/custom_nodes/ComfyUI-LoRA-Backup/
       __init__.py
       web/
           lora_backup.js
   ```

3. Restart ComfyUI and **reload the browser page (F5)** so the button script is loaded.

## Usage

1. Add the node: right-click → *Add Node → utils → "LoRA Backup (copy used LoRAs)"*
2. Set `target_folder` to your destination, e.g. `E:/LoRA_Favorites` (use forward slashes or double backslashes on Windows)
3. Generate as usual. When a LoRA combination turns out great, click **📂 Copy now** — done.

The result is shown as a toast notification (e.g. "2 copied, 1 already present") and logged in the ComfyUI console.

### Node options

| Option | Default | Description |
|---|---|---|
| `target_folder` | `D:/LoRA_Favorites` | Destination folder. Created automatically if it does not exist. |
| `keep_subfolders` | on | Recreate the subfolder structure of your `loras` directory in the target folder. |
| `skip_existing` | on | Skip files that already exist in the target folder with the same size. |
| `auto_run` | off | If enabled, the node additionally copies on every queue run. Off = button only. |
| `trigger` (input) | – | Optional. Connect any output (e.g. the decoded image) to make the node run *after* generation in auto mode. Not needed for the button. |

## How it works

The button reads the current workflow directly from the browser, converts it to the API prompt format and sends it to a small server endpoint (`/lora_backup/copy`). The endpoint scans all node inputs for LoRA file names that exist in your `loras` folder, filters out disabled entries (`on`/`enabled`/`switch` fields), and copies the remaining files with `shutil.copy2` (timestamps preserved). Nothing is ever deleted or moved — files are only copied.

## Compatibility

- ComfyUI on Windows, Linux and macOS (developed and tested on Windows 11)
- Tested with the standard LoraLoader and rgthree's Power Lora Loader
- Recognized LoRA file extensions: `.safetensors`, `.ckpt`, `.pt`, `.pth`, `.bin`

## License

MIT — see [LICENSE](LICENSE).
