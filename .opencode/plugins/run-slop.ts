import { isAbsolute, resolve } from "node:path"
import { Plugin } from "@opencode/plugin"

const ENTRYPOINT = "sloperator.py"
// --no-active ignores an inherited VIRTUAL_ENV and uses the project's own .venv.
// Without it uv warns on stderr about the mismatch, which would pollute the tool's stderr.
const UV_FLAGS = ["uv", "run", "--no-active"]

export default Plugin.define({
  id: "run-slop",
  async setup(ctx) {
    const root = ctx.location.directory

    await ctx.tool.transform((editor) => {
      editor.add({
        name: "run_slop",
        description:
          "Run a SlopLang program with Sloperator and report its stdout, stderr, and exit code as JSON. " +
          "The path may be relative to the project root or absolute. A nonzero exit code means SlopLang " +
          "reported a lexical, syntax, or runtime error, which is written to stderr.",
        input: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description: "Path to the .slop file to run, relative to the project root or absolute.",
            },
          },
          required: ["path"],
          additionalProperties: false,
        },
        output: {
          type: "object",
          properties: {
            stdout: { type: "string" },
            stderr: { type: "string" },
            exitCode: { type: "integer" },
          },
          required: ["stdout", "stderr", "exitCode"],
          additionalProperties: false,
        },
        options: { codemode: false },
        async execute(input, context) {
          const requested = String((input as { path?: string }).path ?? "").trim()
          if (!requested) throw new Error("a 'path' to a .slop file is required")

          const target = isAbsolute(requested) ? requested : resolve(root, requested)
          if (!(await Bun.file(target).exists())) {
            throw new Error(`no such file: ${target}`)
          }

          await context.progress({ status: "running", path: target })

          const proc = Bun.spawn([...UV_FLAGS, ENTRYPOINT, target], {
            cwd: root,
            stdin: "ignore",
            stdout: "pipe",
            stderr: "pipe",
          })

          const [stdout, stderr, exitCode] = await Promise.all([
            new Response(proc.stdout).text(),
            new Response(proc.stderr).text(),
            proc.exited,
          ])

          const result = { stdout, stderr, exitCode }
          return {
            content: JSON.stringify(result, null, 2),
            output: result,
            metadata: result,
          }
        },
      })
    })
  },
})
