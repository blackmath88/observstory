// Static host for browser tests: serves the production build under GitHub-Pages-like project
// subpaths, each with its own fixture data in ./data/, exactly as the Action lays it out.
//   /hackathon/ · /quiet/ · /broken/
import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../..", import.meta.url));
const client = process.env.OBSERVSTORY_PREBUILT ? join(root, "release") : join(root, "dist", "client");
const types = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml" };
const port = Number(process.env.PORT ?? 4319);

createServer((req, res) => {
  const url = new URL(req.url ?? "/", "http://x");
  const [, site, ...rest] = url.pathname.split("/");
  const sub = rest.join("/") || "index.html";
  const dataRoot =
    site === "live" && process.env.OBSERVSTORY_LIVE_DATA ? process.env.OBSERVSTORY_LIVE_DATA : join(root, "fixtures", site ?? "", "data");
  const file = sub.startsWith("data/") ? join(dataRoot, sub.slice(5)) : join(client, sub);
  if (!site || normalize(file) !== file || !existsSync(file) || statSync(file).isDirectory()) {
    res.writeHead(404).end("not found");
    return;
  }
  res.writeHead(200, { "content-type": types[extname(file)] ?? "application/octet-stream" });
  createReadStream(file).pipe(res);
}).listen(port, "127.0.0.1", () => console.log(`serving on ${port}`));
