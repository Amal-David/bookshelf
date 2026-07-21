import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const AMBIENT_SCRIPT = join(ROOT, "hooks", "ambient.py");
const AMBIENT_ENV_KEYS = [
  "PATH",
  "HOME",
  "TMPDIR",
  "TMP",
  "TEMP",
  "LANG",
  "LC_ALL",
  "XDG_DATA_HOME",
  "BOOKSHELF_AMBIENT_ENABLED",
  "BOOKSHELF_AMBIENT_CADENCE",
  "BOOKSHELF_DATA_HOME",
] as const;

function ambientEnvironment(): Record<string, string> {
  const environment: Record<string, string> = {};
  for (const key of AMBIENT_ENV_KEYS) {
    const value = process.env[key];
    if (value) environment[key] = value;
  }
  return environment;
}

export default function bookshelf(pi: ExtensionAPI) {
  pi.on("agent_end", async (_event, ctx) => {
    try {
      const result = await pi.exec(
        "python3",
        [AMBIENT_SCRIPT, "--host", "pi", "--plain", "--no-event"],
        { timeout: 5000, env: ambientEnvironment() },
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
