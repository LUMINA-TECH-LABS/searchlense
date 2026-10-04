# Using searchlense from plain Java (no libraries)

This is the self-bootstrapping pattern. On first run, your Java program
silently creates a Python virtual environment under the user's home
directory and installs the searchlense wheel from its GitHub Release. Then
it spawns `python -m searchlense.bridge` and talks JSON to it over
stdin/stdout.

No Maven. No Gradle. No external JARs. Only the JDK.

## SearchlenseBridge.java

```java
import java.io.*;
import java.nio.file.*;
import java.util.concurrent.*;

public class SearchlenseBridge implements AutoCloseable {

    private final Process process;
    private final BufferedWriter stdin;
    private final BufferedReader stdout;

    private static final String VENV_DIR =
        System.getProperty("user.home") + File.separator + ".searchlense" + File.separator + "venv";

    private static final String WHEEL_URL =
        "https://github.com/<owner>/searchlense/releases/download/v0.1.0/searchlense-0.1.0-py3-none-any.whl";

    public SearchlenseBridge() throws IOException, InterruptedException {
        ensureInstalled();
        String python = venvPython();
        ProcessBuilder pb = new ProcessBuilder(python, "-m", "searchlense.bridge");
        pb.redirectErrorStream(false); // keep stderr for logs, stdout for JSON
        pb.redirectError(ProcessBuilder.Redirect.INHERIT);
        this.process = pb.start();
        this.stdin = new BufferedWriter(new OutputStreamWriter(process.getOutputStream()));
        this.stdout = new BufferedReader(new InputStreamReader(process.getInputStream()));
    }

    private static String venvPython() {
        String exe = System.getProperty("os.name").toLowerCase().contains("win")
            ? "Scripts\\python.exe"
            : "bin/python";
        return VENV_DIR + File.separator + exe;
    }

    private static void ensureInstalled() throws IOException, InterruptedException {
        if (Files.exists(Paths.get(venvPython()))) {
            return; // already installed
        }
        // 1. create venv
        run("python", "-m", "venv", VENV_DIR);
        // 2. upgrade pip
        run(venvPython(), "-m", "pip", "install", "--upgrade", "pip");
        // 3. install the wheel from GitHub Release
        run(venvPython(), "-m", "pip", "install", WHEEL_URL);
    }

    private static void run(String... cmd) throws IOException, InterruptedException {
        Process p = new ProcessBuilder(cmd).inheritIO().start();
        int code = p.waitFor();
        if (code != 0) {
            throw new IOException("command failed (" + code + "): " + String.join(" ", cmd));
        }
    }

    public void send(String json) throws IOException {
        stdin.write(json);
        stdin.newLine();
        stdin.flush();
    }

    public String readLine() throws IOException {
        return stdout.readLine();
    }

    /** Blocking pause check for Mode B. Call inside your agent's loop. */
    public void checkpoint() throws IOException, InterruptedException {
        send("{\"cmd\":\"checkpoint\"}");
        String line;
        while ((line = readLine()) != null) {
            if (line.contains("\"ack\":\"checkpoint\"")) return;
            // You can also dispatch other events here if you want.
        }
    }

    @Override
    public void close() throws IOException {
        try { send("{\"cmd\":\"quit\"}"); } catch (IOException ignored) {}
        stdin.close();
        try { process.waitFor(5, TimeUnit.SECONDS); } catch (InterruptedException ignored) {}
        process.destroyForcibly();
    }

    public static void main(String[] args) throws Exception {
        try (SearchlenseBridge bridge = new SearchlenseBridge()) {
            bridge.send("{\"cmd\":\"run\",\"query\":\"quantum computing\",\"provider\":\"demo\"}");
            String line;
            while ((line = bridge.readLine()) != null) {
                System.out.println("EVENT: " + line);
                if (line.contains("\"type\":\"session_end\"")) break;
            }
        }
    }
}
```

## What the user sees

Nothing. The first time your Java agent runs, it takes ~30 seconds to create
the venv and install the wheel. After that, startup is instant because the
venv is cached in `~/.searchlense/venv`.

## Requirements

- Python 3.10+ must be on PATH (`python` or `python3`).
- Network access on first run (to fetch the wheel from GitHub Releases).
- After the first run, both are only needed if you reinstall.

## Mode B (cooperative pause)

Call `bridge.checkpoint()` inside your agent's loop. It blocks until the
user's UI (or the agent) requests resume. This is the Java equivalent of
`await session.checkpoint()` in Python.
