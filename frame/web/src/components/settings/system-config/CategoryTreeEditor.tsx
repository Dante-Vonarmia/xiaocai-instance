import { Button, Input, Tag, Typography } from 'antd'
import type { CategoryOwnerNode } from './domain-assets-model'
import './category-tree-editor.css'

type CategoryEditorProps = {
  categoryTree: CategoryOwnerNode[]
  editable: boolean
  onChange: (tree: CategoryOwnerNode[]) => void
}

function replaceAt<T>(items: T[], index: number, value: T): T[] {
  return items.map((item, currentIndex) => (currentIndex === index ? value : item))
}

function removeAt<T>(items: T[], index: number): T[] {
  return items.filter((_, currentIndex) => currentIndex !== index)
}

function updateOwner(
  tree: CategoryOwnerNode[],
  ownerIndex: number,
  patch: Partial<CategoryOwnerNode>,
): CategoryOwnerNode[] {
  return replaceAt(tree, ownerIndex, { ...tree[ownerIndex], ...patch })
}

function CategoryHeader(props: {
  tree: CategoryOwnerNode[]
  editable: boolean
  onChange: (tree: CategoryOwnerNode[]) => void
}) {
  return (
    <div className="settings-category-tree-header">
      <div>
        <Typography.Text strong>品类关系</Typography.Text>
        <Typography.Paragraph className="settings-domain-copy" type="secondary">
          采购负责类 → 一级品类 → 二级品类
        </Typography.Paragraph>
      </div>
      {props.editable ? (
        <Button onClick={() => props.onChange([...props.tree, { name: '', level1: [] }])}>
          添加负责类
        </Button>
      ) : null}
    </div>
  )
}

function Level2Rows(props: {
  items: string[]
  editable: boolean
  onChange: (items: string[]) => void
}) {
  if (!props.editable) {
    return (
      <div className="settings-category-level2-list">
        {props.items.length ? props.items.map((item, index) => <Tag key={`${item}-${index}`}>{item}</Tag>) : <Tag>-</Tag>}
      </div>
    )
  }

  return (
    <div className="settings-category-level2-editor">
      {props.items.map((item, index) => (
        <div className="settings-category-level2-row" key={`${item}-${index}`}>
          <Input value={item} placeholder="二级品类" onChange={(event) => props.onChange(replaceAt(props.items, index, event.target.value))} />
          <Button danger onClick={() => props.onChange(removeAt(props.items, index))}>删除</Button>
        </div>
      ))}
      <Button onClick={() => props.onChange([...props.items, ''])}>添加二级品类</Button>
    </div>
  )
}

function OwnerCard(props: {
  owner: CategoryOwnerNode
  ownerIndex: number
  editable: boolean
  tree: CategoryOwnerNode[]
  onChange: (tree: CategoryOwnerNode[]) => void
}) {
  const setOwner = (patch: Partial<CategoryOwnerNode>) => {
    props.onChange(updateOwner(props.tree, props.ownerIndex, patch))
  }
  const setLevel1 = (level1Index: number, level1: CategoryOwnerNode['level1'][number]) => {
    setOwner({ level1: replaceAt(props.owner.level1, level1Index, level1) })
  }

  return (
    <section className="settings-category-owner-card">
      <div className="settings-category-owner-title">
        {props.editable ? (
          <Input value={props.owner.name} placeholder="采购负责类" onChange={(event) => setOwner({ name: event.target.value })} />
        ) : <Typography.Text strong>{props.owner.name || '-'}</Typography.Text>}
        <Tag>{props.owner.level1.length}</Tag>
        {props.editable ? (
          <Button danger onClick={() => props.onChange(removeAt(props.tree, props.ownerIndex))}>删除</Button>
        ) : null}
      </div>

      <div className="settings-category-level1-list">
        {props.owner.level1.map((level1, level1Index) => (
          <div className="settings-category-level1-row" key={`${level1.name}-${level1Index}`}>
            <div className="settings-category-level1-title">
              {props.editable ? (
                <Input
                  value={level1.name}
                  placeholder="一级品类"
                  onChange={(event) => setLevel1(level1Index, { ...level1, name: event.target.value })}
                />
              ) : <Typography.Text>{level1.name || '-'}</Typography.Text>}
              <Tag>{level1.level2Names.length}</Tag>
              {props.editable ? (
                <Button danger onClick={() => setOwner({ level1: removeAt(props.owner.level1, level1Index) })}>删除</Button>
              ) : null}
            </div>
            <Level2Rows
              items={level1.level2Names}
              editable={props.editable}
              onChange={(items) => setLevel1(level1Index, { ...level1, level2Names: items })}
            />
          </div>
        ))}
      </div>

      {props.editable ? (
        <Button onClick={() => setOwner({ level1: [...props.owner.level1, { name: '', level2Names: [] }] })}>
          添加一级品类
        </Button>
      ) : null}
    </section>
  )
}

function CategoryEditor({ categoryTree, editable, onChange }: CategoryEditorProps) {
  return (
    <div className="settings-category-tree">
      <CategoryHeader tree={categoryTree} editable={editable} onChange={onChange} />
      <div className="settings-category-owner-grid">
        {categoryTree.map((owner, ownerIndex) => (
          <OwnerCard
            key={`${owner.name}-${ownerIndex}`}
            owner={owner}
            ownerIndex={ownerIndex}
            editable={editable}
            tree={categoryTree}
            onChange={onChange}
          />
        ))}
      </div>
    </div>
  )
}

export default CategoryEditor
