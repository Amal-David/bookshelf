import assert from "node:assert/strict";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the complete Bookshelf landing page", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(
    html,
    /<title>Bookshelf — Book quotes inside Codex and Claude Code<\/title>/i,
  );
  assert.match(html, /Let the terminal/);
  assert.match(html, /widen your world/);
  assert.match(html, /Instead of staring at another tool call/);
  assert.match(html, /Codex Desktop \+ CLI/);
  assert.match(html, /bookshelf quote --intent refactor/);
  assert.match(html, /Do nothing which is of no use/);
  assert.match(html, /Accessible transcript/);
  assert.match(html, /Claude Code 2\.1\.217/);
  assert.match(html, /Opus 4\.8/);
  assert.match(html, /moonshot-with-unit-tests/);
  assert.match(html, /oxygen, return fuel, and one honest spreadsheet/i);
  assert.match(html, /autoplay=""/i);
  assert.doesNotMatch(html, /Real Stop-hook CLI capture|real isolated CLI capture/);
  assert.match(html, /3,124/);
  assert.match(html, /3,111/);
  assert.match(html, /1,117/);
  assert.match(html, /949/);
  assert.match(html, /585/);
  assert.match(html, /2,539/);
  assert.match(html, /Codex/);
  assert.match(html, /Claude/);
  assert.match(html, /Hermes/);
  assert.match(html, /Pi/);
  assert.match(html, /bookshelf-demo\.mp4/);
  assert.match(html, /github\.com\/Amal-David\/bookshelf/);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape/);
});
