import { Card, Descriptions } from 'antd'
import { getCurrentUserId } from '@/services/api'

type ProfilePanelProps = {
  projectId: string
}

function ProfilePanel({ projectId }: ProfilePanelProps) {
  const userId = getCurrentUserId() || 'anonymous-user'

  return (
    <Card title="个人信息" bordered={false}>
      <Descriptions column={1} size="small" labelStyle={{ width: 140 }}>
        <Descriptions.Item label="用户 ID">{userId}</Descriptions.Item>
        <Descriptions.Item label="当前项目">{projectId}</Descriptions.Item>
        <Descriptions.Item label="角色">采购工作台用户</Descriptions.Item>
      </Descriptions>
    </Card>
  )
}

export default ProfilePanel
