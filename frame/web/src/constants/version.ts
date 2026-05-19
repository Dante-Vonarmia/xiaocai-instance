import packageJson from '../../package.json'

const FLARE_CHAT_CORE_PACKAGE = 'flare-chat-core'

export const FLARE_VERSION = packageJson.dependencies[FLARE_CHAT_CORE_PACKAGE]
