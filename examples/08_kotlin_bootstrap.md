# Using searchlense from Kotlin (no libraries)

Same self-bootstrapping pattern as the Java example. Kotlin's `ProcessBuilder`
is the JDK one, so no extra dependencies are needed. Coroutines make reading
the stdout stream clean, but you can also use plain blocking reads.

## SearchlenseBridge.kt

```kotlin
import java.io.BufferedReader
import java.io.BufferedWriter
import java.io.File
import java.io.InputStreamReader
import java.io.OutputStreamWriter

class SearchlenseBridge : AutoCloseable {

    private val process: Process
    private val stdin: BufferedWriter
    private val stdout: BufferedReader

    init {
        ensureInstalled()
        val pb = ProcessBuilder(venvPython(), "-m", "searchlense.bridge")
        pb.redirectError(ProcessBuilder.Redirect.INHERIT)
        process = pb.start()
        stdin = BufferedWriter(OutputStreamWriter(process.outputStream))
        stdout = BufferedReader(InputStreamReader(process.inputStream))
    }

    fun send(json: String) {
        stdin.write(json)
        stdin.newLine()
        stdin.flush()
    }

    fun readLine(): String? = stdout.readLine()

    /** Blocking pause check for Mode B. Call inside your agent's loop. */
    fun checkpoint() {
        send("""{"cmd":"checkpoint"}""")
        while (true) {
            val line = readLine() ?: return
            if (line.contains("\"ack\":\"checkpoint\"")) return
        }
    }

    override fun close() {
        try { send("""{"cmd":"quit"}""") } catch (_: Exception) {}
        stdin.close()
        process.waitFor()
        process.destroyForcibly()
    }

    companion object {
        private val VENV_DIR = File(System.getProperty("user.home"), ".searchlense/venv")

        private const val WHEEL_URL =
            "https://github.com/LUMINA-TECH-LABS/searchlense/releases/download/v0.1.0/searchlense-0.1.0-py3-none-any.whl"

        private fun venvPython(): String {
            val exe = if (System.getProperty("os.name").lowercase().contains("win"))
                "Scripts/python.exe" else "bin/python"
            return File(VENV_DIR, exe).absolutePath
        }

        private fun ensureInstalled() {
            if (File(venvPython()).exists()) return
            run("python", "-m", "venv", VENV_DIR.absolutePath)
            run(venvPython(), "-m", "pip", "install", "--upgrade", "pip")
            run(venvPython(), "-m", "pip", "install", WHEEL_URL)
        }

        private fun run(vararg cmd: String) {
            val p = ProcessBuilder(*cmd).inheritIO().start()
            val code = p.waitFor()
            check(code == 0) { "command failed ($code): ${cmd.joinToString(" ")}" }
        }
    }
}

fun main() {
    SearchlenseBridge().use { bridge ->
        bridge.send("""{"cmd":"run","query":"quantum computing","provider":"demo"}""")
        while (true) {
            val line = bridge.readLine() ?: break
            println("EVENT: $line")
            if (line.contains("\"type\":\"session_end\"")) break
        }
    }
}
```

## Notes

- Kotlin coroutines are not required; the blocking loop above is fine.
- If you want to read on a background thread and expose a Flow, wrap
  `readLine()` in `flow { ... }.flowOn(Dispatchers.IO)`.
- The `checkpoint()` call is the Mode B hook. Same semantics as Python.
