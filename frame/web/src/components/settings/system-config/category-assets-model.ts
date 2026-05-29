export type CategoryLevel1Node = {
  name: string
  level2Names: string[]
}

export type CategoryOwnerNode = {
  name: string
  level1: CategoryLevel1Node[]
}

export type CategoryAssetSummary = {
  ownerCount: number
  level1Count: number
  level2Count: number
  ownerNames: string[]
  level1Names: string[]
  level2Names: string[]
  categoryTree: CategoryOwnerNode[]
}

type CategoryCounts = Pick<CategoryAssetSummary, 'ownerCount' | 'level1Count' | 'level2Count'>

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {}
}

function asString(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : []
}

function readNumber(text: string, key: string): number {
  const match = text.match(new RegExp(`${key}:\\s*(\\d+)`))
  return match ? Number(match[1]) : 0
}

function readCounts(text: string): CategoryCounts {
  return {
    ownerCount: readNumber(text, '采购负责类数量'),
    level1Count: readNumber(text, '一级品类数量'),
    level2Count: readNumber(text, '二级品类数量'),
  }
}

function readName(line: string, spaces: number): string {
  const match = line.match(new RegExp(`^ {${spaces}}- 名称:\\s*(.+)$`))
  return match?.[1]?.trim() || ''
}

export function flattenCategoryTree(tree: CategoryOwnerNode[]) {
  const ownerNames = tree.map((owner) => owner.name).filter(Boolean)
  const level1Names = tree.flatMap((owner) => owner.level1.map((item) => item.name)).filter(Boolean)
  const level2Names = tree
    .flatMap((owner) => owner.level1.flatMap((item) => item.level2Names))
    .filter(Boolean)
  return { ownerNames, level1Names, level2Names }
}

export function countCategoryTree(tree: CategoryOwnerNode[]): CategoryCounts {
  const flat = flattenCategoryTree(tree)
  return {
    ownerCount: flat.ownerNames.length,
    level1Count: flat.level1Names.length,
    level2Count: flat.level2Names.length,
  }
}

export function parseCategoryAsset(text: string): CategoryAssetSummary {
  const taxonomy = parseTaxonomyAsset(text)
  if (taxonomy) {
    return taxonomy
  }

  const categoryTree: CategoryOwnerNode[] = []
  let currentOwner: CategoryOwnerNode | null = null
  let currentLevel1: CategoryLevel1Node | null = null

  text.split('\n').forEach((line) => {
    const ownerName = readName(line, 2)
    if (ownerName) {
      currentOwner = { name: ownerName, level1: [] }
      currentLevel1 = null
      categoryTree.push(currentOwner)
      return
    }

    const level1Name = readName(line, 6)
    if (level1Name && currentOwner) {
      currentLevel1 = { name: level1Name, level2Names: [] }
      currentOwner.level1.push(currentLevel1)
      return
    }

    const level2Name = readName(line, 10)
    if (level2Name && currentLevel1) {
      currentLevel1.level2Names.push(level2Name)
    }
  })

  const flat = flattenCategoryTree(categoryTree)
  return {
    ...readCounts(text),
    ownerNames: flat.ownerNames,
    level1Names: flat.level1Names,
    level2Names: flat.level2Names,
    categoryTree,
  }
}

function parseTaxonomyAsset(text: string): CategoryAssetSummary | null {
  try {
    const payload = JSON.parse(text) as Record<string, unknown>
    const categories = asRecord(payload.procurement_categories)
    if (!Object.keys(categories).length) {
      return null
    }
    const categoryTree = Object.entries(categories).map(([ownerName, level1Value]) => {
      const level1Record = asRecord(level1Value)
      return {
        name: ownerName,
        level1: Object.entries(level1Record).map(([level1Name, level2Value]) => ({
          name: level1Name,
          level2Names: asArray(level2Value).map(asString).filter(Boolean),
        })),
      }
    })
    const flat = flattenCategoryTree(categoryTree)
    return {
      ...countCategoryTree(categoryTree),
      ownerNames: flat.ownerNames,
      level1Names: flat.level1Names,
      level2Names: flat.level2Names,
      categoryTree,
    }
  } catch {
    return null
  }
}

export function readCategoryTree(value: unknown): CategoryOwnerNode[] {
  return asArray(value)
    .map((owner) => {
      const ownerRecord = asRecord(owner)
      return {
        name: asString(ownerRecord.name),
        level1: asArray(ownerRecord.level1)
          .map((level1) => {
            const level1Record = asRecord(level1)
            return {
              name: asString(level1Record.name),
              level2Names: asArray(level1Record.level2Names).map(asString).filter(Boolean),
            }
          })
          .filter((level1) => level1.name || level1.level2Names.length),
      }
    })
    .filter((owner) => owner.name || owner.level1.length)
}

export function normalizeCategoryTreeForPayload(tree: CategoryOwnerNode[]): CategoryOwnerNode[] {
  return tree
    .map((owner) => ({
      name: owner.name.trim(),
      level1: owner.level1
        .map((level1) => ({
          name: level1.name.trim(),
          level2Names: level1.level2Names.map((item) => item.trim()).filter(Boolean),
        }))
        .filter((level1) => level1.name || level1.level2Names.length),
    }))
    .filter((owner) => owner.name || owner.level1.length)
}
