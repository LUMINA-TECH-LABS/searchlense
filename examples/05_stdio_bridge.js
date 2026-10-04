/**
 * Example: drive searchlense from Node.js via the stdio bridge.
 *
 * No npm packages. Uses only child_process and readline from Node core.
 * The same pattern works in any language that can spawn a subprocess.
 *
 * Run:
 *     node examples/05_stdio_bridge.js
 *
 * Assumes `python -m searchlense.bridge` is on PATH (i.e. searchlense is
 * installed in the active Python environment).
 */

const { spawn } = require("node:child_process");
const readline = require("node:readline");

const bridge = spawn("python", ["-m", "searchlense.bridge"], {
  stdio: ["pipe", "pipe", "inherit"],
});

const rl = readline.createInterface({ input: bridge.stdout });

function send(obj) {
  bridge.stdin.write(JSON.stringify(obj) + "\n");
}

rl.on("line", (line) => {
  let msg;
  try {
    msg = JSON.parse(line);
  } catch (err) {
    console.error("bad line from bridge:", line);
    return;
  }

  if (msg.ack) {
    console.error(`[ack] ${msg.ack} ok=${msg.ok}`);
    if (msg.ack === "run") {
      // After the run begins, schedule a pause/resume demo.
      setTimeout(() => send({ cmd: "pause" }), 800);
      setTimeout(() => send({ cmd: "rewind", steps: 2 }), 1800);
      setTimeout(() => send({ cmd: "resume" }), 2600);
    }
    if (msg.ack === "quit") {
      bridge.stdin.end();
    }
    return;
  }

  if (msg.error) {
    console.error("[bridge error]", msg.error);
    return;
  }

  console.log(`[event] #${msg.sequence} ${msg.type}`, msg.payload);
});

bridge.on("exit", (code) => {
  console.log(`bridge exited with code ${code}`);
  process.exit(code ?? 0);
});

send({ cmd: "ping" });
send({ cmd: "run", query: "cinematic search demo", provider: "demo" });

// Let the demo play, then quit.
setTimeout(() => send({ cmd: "quit" }), 6000);
