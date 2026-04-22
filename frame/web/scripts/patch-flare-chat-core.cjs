const fs = require('fs')
const path = require('path')

const defaultTarget = path.resolve(__dirname, '../dist/assets')

function resolveTarget(argvTarget) {
  if (argvTarget) {
    return path.resolve(process.cwd(), argvTarget)
  }
  return defaultTarget
}

function collectFiles(targetPath) {
  if (!fs.existsSync(targetPath)) {
    throw new Error(`patch target not found: ${targetPath}`)
  }

  const stat = fs.statSync(targetPath)
  if (stat.isDirectory()) {
    return fs.readdirSync(targetPath)
      .filter((name) => name.endsWith('.js'))
      .map((name) => path.join(targetPath, name))
  }

  return [targetPath]
}

function buildAuthHeadersExpression() {
  return '(()=>{const fetchAuthToken=(()=>{try{return typeof window<"u"&&window?.localStorage?String(window.localStorage.getItem("access_token")||"").trim():""}catch{return""}})();return{"Content-Type":"application/json",...fetchAuthToken?{Authorization:`Bearer ${fetchAuthToken}`}:{}}})()'
}

function patchContent(source) {
  let patched = source
  let changes = 0
  const authHeaders = buildAuthHeadersExpression()

  const replacements = [
    {
      pattern: /(await fetch\([^)]*?"\/chat\/stream"\),\{method:"POST",)headers:\{"Content-Type":"application\/json"\},body:/g,
      replacement: `$1headers:${authHeaders},body:`,
    },
    {
      pattern: /(await fetch\([^)]*?"\/chat\/action"\),\{method:"POST",)headers:\{"Content-Type":"application\/json"\},body:/g,
      replacement: `$1headers:${authHeaders},body:`,
    },
    {
      pattern: /(await fetch\([^)]*?"\/chat\/stream"\),\s*\{\s*method:\s*"POST",\s*)headers:\s*\{\s*"Content-Type":\s*"application\/json"\s*\},\s*body:/g,
      replacement: `$1headers: ${authHeaders}, body:`,
    },
    {
      pattern: /(await fetch\([^)]*?"\/chat\/action"\),\s*\{\s*method:\s*"POST",\s*)headers:\s*\{\s*"Content-Type":\s*"application\/json"\s*\},\s*body:/g,
      replacement: `$1headers: ${authHeaders}, body:`,
    },
  ]

  for (const { pattern, replacement } of replacements) {
    patched = patched.replace(pattern, (...args) => {
      changes += 1
      return args[0].replace(pattern, replacement)
    })
  }

  return { patched, changes }
}

const target = resolveTarget(process.argv[2])
const files = collectFiles(target)
let totalChanges = 0

for (const filePath of files) {
  const original = fs.readFileSync(filePath, 'utf8')
  const { patched, changes } = patchContent(original)
  if (changes > 0) {
    fs.writeFileSync(filePath, patched)
    totalChanges += changes
  }
}

if (totalChanges === 0) {
  throw new Error(`[patch-flare-chat-core] no stream/action transport patch applied for target: ${target}`)
}

console.log(`[patch-flare-chat-core] applied ${totalChanges} replacement(s) to ${target}`)
