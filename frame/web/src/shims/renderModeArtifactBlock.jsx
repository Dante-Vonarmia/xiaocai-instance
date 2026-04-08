import React from 'react';
import { Card, Space, Typography } from 'antd';

const { Paragraph, Text } = Typography;

function getArtifactContent(payload) {
  if (typeof payload?.content === 'string' && payload.content.trim()) {
    return payload.content;
  }

  if (typeof payload?.text === 'string' && payload.text.trim()) {
    return payload.text;
  }

  if (typeof payload?.summary === 'string' && payload.summary.trim()) {
    return payload.summary;
  }

  try {
    return JSON.stringify(payload || {}, null, 2);
  } catch {
    return '';
  }
}

export function renderModeArtifactBlock({ item, themeTokens }) {
  const payload = item?.payload || {};
  const title = payload?.title || item?.type || 'artifact';
  const content = getArtifactContent(payload);

  return (
    <Card
      className="flare-ui-card"
      size="small"
      style={{
        background: themeTokens?.surfaceBg,
        borderColor: themeTokens?.surfaceBorder,
      }}
      styles={{ body: { padding: 14 } }}
    >
      <Space direction="vertical" size={8} style={{ width: '100%' }}>
        <Text strong style={{ color: themeTokens?.textPrimary }}>
          {title}
        </Text>
        <Paragraph
          style={{
            color: themeTokens?.textSecondary,
            marginBottom: 0,
            whiteSpace: 'pre-wrap',
          }}
        >
          {content}
        </Paragraph>
      </Space>
    </Card>
  );
}

export default renderModeArtifactBlock;
