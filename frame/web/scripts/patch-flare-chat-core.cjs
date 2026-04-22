const fs = require('fs')
const path = require('path')

const distPath = path.resolve(__dirname, '../node_modules/@flare/chat-core/dist/index.js')

function applyPatch(source) {
  const streamNeedle = `const f = await fetch(fn(e, "/chat/stream"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },`
  const streamReplacement = `const fetchAuthToken = (() => {
    try {
      return typeof window < "u" && window?.localStorage ? String(window.localStorage.getItem("access_token") || "").trim() : "";
    } catch {
      return "";
    }
  })(), f = await fetch(fn(e, "/chat/stream"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...fetchAuthToken ? { Authorization: \`Bearer \${fetchAuthToken}\` } : {}
    },`

  const actionNeedle = `const a = await fetch(fn(e, "/chat/action"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },`
  const actionReplacement = `const fetchAuthToken = (() => {
    try {
      return typeof window < "u" && window?.localStorage ? String(window.localStorage.getItem("access_token") || "").trim() : "";
    } catch {
      return "";
    }
  })(), a = await fetch(fn(e, "/chat/action"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...fetchAuthToken ? { Authorization: \`Bearer \${fetchAuthToken}\` } : {}
    },`

  let patched = source

  if (patched.includes(streamNeedle)) {
    patched = patched.replace(streamNeedle, streamReplacement)
  }

  if (patched.includes(actionNeedle)) {
    patched = patched.replace(actionNeedle, actionReplacement)
  }

  return patched
}

if (!fs.existsSync(distPath)) {
  throw new Error(`flare-chat-core dist not found: ${distPath}`)
}

const original = fs.readFileSync(distPath, 'utf8')
const patched = applyPatch(original)

if (patched === original) {
  console.log('[patch-flare-chat-core] no changes applied')
  process.exit(0)
}

fs.writeFileSync(distPath, patched)
console.log('[patch-flare-chat-core] patched Authorization forwarding for chat stream/action')
