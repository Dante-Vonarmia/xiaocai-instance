from unittest.mock import patch

from fastapi.testclient import TestClient

from xiaocai_instance_api.app import create_app


def _token(client: TestClient, user_id: str) -> str:
    response = client.post('/auth/exchange', json={'mock': True, 'mock_user_id': user_id})
    assert response.status_code == 200
    return response.json()['access_token']


def test_release_regression_requirement_sourcing_and_usage(monkeypatch):
    monkeypatch.setenv('DAILY_MESSAGE_LIMIT', '10')
    monkeypatch.setenv('DAILY_PROJECT_MESSAGE_LIMIT', '6')

    app = create_app()
    client = TestClient(app)

    token = _token(client, 'release-user')

    bind_response = client.post(
        '/projects/bind',
        headers={'Authorization': f'Bearer {token}'},
        json={'project_id': 'proj-release-1'},
    )
    assert bind_response.status_code == 200

    with patch('xiaocai_instance_api.chat.kernel_client.KernelClient.chat_run') as mock_chat_run:
        mock_chat_run.side_effect = [
            {
                'message': '需求梳理完成',
                'cards': [{'type': 'requirement-form', 'data': {'step': 'collect'}}],
                'session_id': 'sess-release-requirement',
                'metadata': {},
            },
            {
                'message': '智能寻源开始',
                'cards': [],
                'session_id': 'sess-release-sourcing',
                'metadata': {},
            },
        ]

        requirement_response = client.post(
            '/chat/run',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'message': '我要采购办公电脑',
                'session_id': 'sess-release-requirement',
                'context': {'project_id': 'proj-release-1', 'mode': 'auto'},
            },
        )
        assert requirement_response.status_code == 200
        requirement_body = requirement_response.json()
        assert requirement_body['message'] == '需求梳理完成'
        assert len(requirement_body['cards']) >= 1

        sourcing_response = client.post(
            '/chat/run',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'message': '帮我找供应商',
                'session_id': 'sess-release-sourcing',
                'context': {'project_id': 'proj-release-1', 'mode': 'intelligent_sourcing'},
            },
        )
        assert sourcing_response.status_code == 200
        sourcing_body = sourcing_response.json()
        assert len(sourcing_body['cards']) == 0

    usage_response = client.get(
        '/projects/usage',
        headers={'Authorization': f'Bearer {token}'},
        params={'project_id': 'proj-release-1'},
    )
    assert usage_response.status_code == 200
    usage_body = usage_response.json()
    assert usage_body['daily_message_used'] >= 2
    assert usage_body['daily_project_message_used'] >= 2
