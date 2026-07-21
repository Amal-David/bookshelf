import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const AMBIENT_SCRIPT = join(ROOT, "hooks", "ambient.py");

export default function bookshelf(pi: ExtensionAPI) {
  pi.on("agent_end", async (_event, ctx) => {
    try {
      const result = await pi.exec(
        "python3",
        [AMBIENT_SCRIPT, "--host", "pi", "--plain"],
        { timeout: 5000 },
      );
      const message = result.stdout.trim();
      if (result.code === 0 && message && ctx.hasUI) {
        ctx.ui.notify(message, "info");
      }
    } catch {
      // A companion must never interrupt the user's agent turn.
    }
  });
}
