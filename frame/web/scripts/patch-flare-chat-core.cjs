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

function toText(value) {
  if (typeof value === 'string' && value.trim()) {
    return value.trim()
  }
  return ''
}

function readJsonFile(filePath) {
  if (!filePath || !fs.existsSync(filePath)) {
    return null
  }
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'))
  } catch {
    return null
  }
}

function loadBrandingPayload() {
  const candidates = [
    process.env.XIAOCAI_BRANDING_FILE,
    path.resolve(process.cwd(), 'domain-packs/branding/instance-branding.json'),
    path.resolve(process.cwd(), '../../domain-packs/branding/instance-branding.json'),
  ].filter(Boolean)

  for (const candidate of candidates) {
    const payload = readJsonFile(candidate)
    if (payload) {
      return payload
    }
  }
  return {}
}

function buildBrandingConfig() {
  const payload = loadBrandingPayload()
  const instance = payload.instance || {}
  const chat = payload.ui?.chat || {}
  const uiLabels = chat.uiLabels || {}
  const productName = toText(uiLabels.product_name)
    || toText(instance.displayName)
    || '小采'
  return {
    customerRoleFallback: process.env.XIAOCAI_BRAND_ROLE_FALLBACK || productName,
    emptyStateDescription: process.env.XIAOCAI_EMPTY_STATE_DESCRIPTION
      || toText(uiLabels.empty_state_description)
      || toText(chat.welcomeMessage)
      || '小采在手，采购不愁。',
    emptyStateTitle: process.env.XIAOCAI_EMPTY_STATE_TITLE
      || toText(uiLabels.empty_state_title)
      || `欢迎来到${productName}`,
    productName: process.env.XIAOCAI_PRODUCT_NAME || productName,
    productTag: process.env.XIAOCAI_PRODUCT_TAG
      || toText(uiLabels.brand_tag)
      || toText(instance.subtitle)
      || 'AI智能采购助手',
  }
}

function buildBrandingReplacements() {
  const branding = buildBrandingConfig()
  return [
    {
      pattern: /"欢迎使用 FLARE"/g,
      replacement: JSON.stringify(branding.emptyStateTitle),
    },
    {
      pattern: /"开始一个新对话。"/g,
      replacement: JSON.stringify(branding.emptyStateDescription),
    },
    {
      pattern: /(customerRoleFallback:\s*)"FLARE"/g,
      replacement: `$1${JSON.stringify(branding.customerRoleFallback)}`,
    },
    {
      pattern: /(resolvedProductName:\s*)"F\.L\.A\.R\.E"/g,
      replacement: `$1${JSON.stringify(branding.productName)}`,
    },
    {
      pattern: /(resolvedProductTag:\s*)"项目协同工作台"/g,
      replacement: `$1${JSON.stringify(branding.productTag)}`,
    },
  ]
}

function buildThemeReplacements() {
  const theme = {
    appBg: process.env.XIAOCAI_APP_BG || '#ffffff',
    appBorder: process.env.XIAOCAI_APP_BORDER || '#ddd6fe',
    appShadow: process.env.XIAOCAI_APP_SHADOW || '0 16px 40px rgba(76, 29, 149, 0.10)',
    sidebarBg: process.env.XIAOCAI_SIDEBAR_BG || '#faf5ff',
    divider: process.env.XIAOCAI_DIVIDER || '#ddd6fe',
    surfaceBgActive: process.env.XIAOCAI_SURFACE_BG_ACTIVE || '#f5f3ff',
    surfaceBorder: process.env.XIAOCAI_SURFACE_BORDER || '#ddd6fe',
    surfaceBorderActive: process.env.XIAOCAI_PRIMARY || '#8b5cf6',
    textMuted: process.env.XIAOCAI_TEXT_MUTED || '#7c6f9f',
    iconNeutral: process.env.XIAOCAI_ICON_NEUTRAL || '#6b5f85',
    iconMuted: process.env.XIAOCAI_ICON_MUTED || '#8b80a8',
    bubbleUserBg: process.env.XIAOCAI_PRIMARY || '#8b5cf6',
    bubbleUserSubtleText: process.env.XIAOCAI_BUBBLE_USER_SUBTLE_TEXT || '#f3e8ff',
    composerBg: process.env.XIAOCAI_COMPOSER_BG || '#ffffff',
    fileTagBg: process.env.XIAOCAI_FILE_TAG_BG || 'rgba(139, 92, 246, 0.12)',
    fileTagBorder: process.env.XIAOCAI_FILE_TAG_BORDER || 'rgba(139, 92, 246, 0.28)',
    fileTagText: process.env.XIAOCAI_FILE_TAG_TEXT || '#6d28d9',
    scenarioCardBgActive: process.env.XIAOCAI_SCENARIO_CARD_BG_ACTIVE || '#f5f3ff',
    scenarioCardBorder: process.env.XIAOCAI_SCENARIO_CARD_BORDER || '#ddd6fe',
    scenarioCardBorderActive: process.env.XIAOCAI_PRIMARY || '#8b5cf6',
    focusOutline: process.env.XIAOCAI_FOCUS_OUTLINE || '0 0 0 3px rgba(139, 92, 246, 0.18)',
  }
  return [
    ['#eef3fb', theme.appBg],
    ['#d4deec', theme.appBorder],
    ['0 16px 40px rgba(15, 23, 42, 0.09)', theme.appShadow],
    ['#f8fbff', theme.sidebarBg],
    ['#dce6f3', theme.divider],
    ['#eaf2ff', theme.surfaceBgActive],
    ['#d4dfef', theme.surfaceBorder],
    ['#3b82f6', theme.surfaceBorderActive],
    ['#7f8ea5', theme.textMuted],
    ['#54637d', theme.iconNeutral],
    ['#8191a8', theme.iconMuted],
    ['#2b6cf3', theme.bubbleUserBg],
    ['#dbe8ff', theme.bubbleUserSubtleText],
    ['#f7faff', theme.composerBg],
    ['rgba(43, 108, 243, 0.12)', theme.fileTagBg],
    ['rgba(43, 108, 243, 0.3)', theme.fileTagBorder],
    ['#1d4ea2', theme.fileTagText],
    ['#eaf2ff', theme.scenarioCardBgActive],
    ['#d4dfef', theme.scenarioCardBorder],
    ['#3b82f6', theme.scenarioCardBorderActive],
    ['0 0 0 3px rgba(59, 130, 246, 0.22)', theme.focusOutline],
  ].map(([from, to]) => ({
    pattern: new RegExp(JSON.stringify(from).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'),
    replacement: JSON.stringify(to),
  }))
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
    {
      pattern: /(c1\(e,"\/chat\/stream"\),[^;]*?await fetch\([^,]+,\{method:[^,]+,)headers:\{"Content-Type":"application\/json"\},body:/g,
      replacement: `$1headers:${authHeaders},body:`,
    },
    {
      pattern: /(c1\(e,"\/chat\/action"\),[^;]*?await fetch\([^,]+,\{method:[^,]+,)headers:\{"Content-Type":"application\/json"\},body:/g,
      replacement: `$1headers:${authHeaders},body:`,
    },
    {
      pattern: /("\/chat\/stream"\),[^;]{0,500}?await fetch\([^,]+,\{method:[^,]+,)headers:\{"Content-Type":"application\/json"\},body:/g,
      replacement: `$1headers:${authHeaders},body:`,
    },
    {
      pattern: /("\/chat\/action"\),[^;]{0,500}?await fetch\([^,]+,\{method:[^,]+,)headers:\{"Content-Type":"application\/json"\},body:/g,
      replacement: `$1headers:${authHeaders},body:`,
    },
  ]

  for (const { pattern, replacement } of replacements) {
    patched = patched.replace(pattern, (...args) => {
      changes += 1
      return args[0].replace(pattern, replacement)
    })
  }

  for (const { pattern, replacement } of buildBrandingReplacements()) {
    patched = patched.replace(pattern, (...args) => {
      changes += 1
      return args[0].replace(pattern, replacement)
    })
  }

  for (const { pattern, replacement } of buildThemeReplacements()) {
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
  console.log(`[patch-flare-chat-core] no legacy stream/action transport patch needed for target: ${target}`)
  process.exit(0)
}

console.log(`[patch-flare-chat-core] applied ${totalChanges} replacement(s) to ${target}`)
