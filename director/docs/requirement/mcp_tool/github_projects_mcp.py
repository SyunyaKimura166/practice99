#!/usr/bin/env python3
"""
GitHub Projects MCP Server using Standard MCP
GitHub Projectsのステータス管理を行うMCPサーバー（FastMCP対応版）
"""

import os
import json
import re
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List
import asyncio
from datetime import datetime

# MCP Server imports
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from pydantic import AnyUrl

def make_github_request(query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """GitHub GraphQL APIにリクエストを送信"""
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise ValueError('GITHUB_TOKEN環境変数が設定されていません')

    url = 'https://api.github.com/graphql'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    data = {'query': query}
    if variables:
        data['variables'] = variables

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f'GitHub API Error: {e.code} - {error_body}')

def get_issue_project_info(issue_node_id: str) -> Dict[str, Any]:
    """
    Issueのプロジェクト情報とステータスを取得します

    Args:
        issue_node_id: IssueのNode ID

    Returns:
        プロジェクト情報とステータスのデータ
    """
    query = """
    query($issueId: ID!) {
      node(id: $issueId) {
        ... on Issue {
          number
          title
          projectItems(first: 10) {
            nodes {
              id
              project {
                id
                title
                number
              }
              fieldValues(first: 20) {
                nodes {
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    name
                    optionId
                    field {
                      ... on ProjectV2SingleSelectField {
                        id
                        name
                        options {
                          id
                          name
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    return make_github_request(query, {'issueId': issue_node_id})

def update_project_status(project_id: str, item_id: str, field_id: str, option_id: str) -> Dict[str, Any]:
    """
    GitHub Projects V2のアイテムのステータスを変更します

    Args:
        project_id: プロジェクトのNode ID
        item_id: プロジェクトアイテムのNode ID
        field_id: ステータスフィールドのNode ID
        option_id: ステータスオプションのNode ID

    Returns:
        更新結果のデータ
    """
    mutation = """
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
      updateProjectV2ItemFieldValue(
        input: {
          projectId: $projectId
          itemId: $itemId
          fieldId: $fieldId
          value: {
            singleSelectOptionId: $optionId
          }
        }
      ) {
        projectV2Item {
          id
          fieldValues(first: 20) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field {
                  ... on ProjectV2SingleSelectField {
                    name
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    variables = {
        'projectId': project_id,
        'itemId': item_id,
        'fieldId': field_id,
        'optionId': option_id
    }

    return make_github_request(mutation, variables)

def get_issue_node_id_from_repo_info(owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
    """
    リポジトリ情報からissueのNode IDを取得します

    Args:
        owner: リポジトリオーナー（ユーザー名またはオーガニゼーション名）
        repo: リポジトリ名
        issue_number: Issue番号

    Returns:
        IssueのNode IDを含む情報
    """
    query = """
    query($owner: String!, $repo: String!, $issueNumber: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $issueNumber) {
          id
          number
          title
          state
        }
      }
    }
    """

    variables = {
        'owner': owner,
        'repo': repo,
        'issueNumber': issue_number
    }

    return make_github_request(query, variables)

def change_issue_status_by_repo_info(owner: str, repo: str, issue_number: int, from_status: str, to_status: str) -> Dict[str, Any]:
    """
    リポジトリ情報を使ってissueのプロジェクトステータスを変更します（一連の処理を自動実行）

    Args:
        owner: リポジトリオーナー（ユーザー名またはオーガニゼーション名）
        repo: リポジトリ名
        issue_number: Issue番号
        from_status: 現在のステータス（検証用）
        to_status: 変更先のステータス

    Returns:
        処理結果（成功/失敗の詳細情報）
    """
    try:
        # 1. issue Node IDを取得
        issue_response = get_issue_node_id_from_repo_info(owner, repo, issue_number)
        if 'errors' in issue_response:
            return {'error': f'Issue取得エラー: {issue_response["errors"]}'}

        issue_data = issue_response.get('data', {}).get('repository', {}).get('issue')
        if not issue_data:
            return {'error': f'Issue #{issue_number} が見つかりません'}

        issue_node_id = issue_data['id']

        # 2. プロジェクト情報を取得
        project_response = get_issue_project_info(issue_node_id)
        if 'errors' in project_response:
            return {'error': f'プロジェクト情報取得エラー: {project_response["errors"]}'}

        project_items = project_response.get('data', {}).get('node', {}).get('projectItems', {}).get('nodes', [])
        if not project_items:
            return {'error': 'プロジェクトにアサインされていません'}

        # 3. 最初のプロジェクトアイテムを使用
        project_item = project_items[0]
        project_id = project_item['project']['id']
        item_id = project_item['id']

        # 4. ステータスフィールドを見つける
        field_values = project_item.get('fieldValues', {}).get('nodes', [])
        status_field = None
        current_status = None

        for field_value in field_values:
            if field_value and 'field' in field_value and field_value.get('field', {}).get('name') == 'Status':
                status_field = field_value['field']
                current_status = field_value.get('name')
                break

        if not status_field:
            return {'error': 'ステータスフィールドが見つかりません'}

        # 5. from_statusの確認
        if current_status != from_status:
            return {
                'error': f'現在のステータス "{current_status}" は期待される "{from_status}" と異なります',
                'current_status': current_status
            }

        # 6. to_statusのオプションIDを見つける
        field_id = status_field['id']
        to_option_id = None

        for option in status_field.get('options', []):
            if option['name'] == to_status:
                to_option_id = option['id']
                break

        if not to_option_id:
            available_statuses = [opt['name'] for opt in status_field.get('options', [])]
            return {
                'error': f'ステータス "{to_status}" が見つかりません',
                'available_statuses': available_statuses
            }

        # 7. ステータスを更新
        update_response = update_project_status(project_id, item_id, field_id, to_option_id)
        if 'errors' in update_response:
            return {'error': f'ステータス更新エラー: {update_response["errors"]}'}

        # 8. 成功レスポンス
        return {
            'success': True,
            'issue': {
                'number': issue_data['number'],
                'title': issue_data['title'],
                'node_id': issue_node_id
            },
            'project': {
                'id': project_id,
                'title': project_item['project']['title']
            },
            'status_change': {
                'from': from_status,
                'to': to_status
            },
            'update_response': update_response
        }

    except Exception as e:
        return {'error': f'処理中にエラーが発生しました: {str(e)}'}

def change_issue_status_by_node_id(issue_node_id: str, from_status: str, to_status: str) -> Dict[str, Any]:
    """
    issueのNode IDを使ってプロジェクトステータスを変更します（一連の処理を自動実行）

    Args:
        issue_node_id: IssueのNode ID
        from_status: 現在のステータス（検証用）
        to_status: 変更先のステータス

    Returns:
        処理結果（成功/失敗の詳細情報）
    """
    try:
        # 1. プロジェクト情報を取得
        project_response = get_issue_project_info(issue_node_id)
        if 'errors' in project_response:
            return {'error': f'プロジェクト情報取得エラー: {project_response["errors"]}'}

        issue_data = project_response.get('data', {}).get('node', {})
        if not issue_data:
            return {'error': 'Issue が見つかりません'}

        project_items = issue_data.get('projectItems', {}).get('nodes', [])
        if not project_items:
            return {'error': 'プロジェクトにアサインされていません'}

        # 2. 最初のプロジェクトアイテムを使用
        project_item = project_items[0]
        project_id = project_item['project']['id']
        item_id = project_item['id']

        # 3. ステータスフィールドを見つける
        field_values = project_item.get('fieldValues', {}).get('nodes', [])
        status_field = None
        current_status = None

        for field_value in field_values:
            if field_value and 'field' in field_value and field_value.get('field', {}).get('name') == 'Status':
                status_field = field_value['field']
                current_status = field_value.get('name')
                break

        if not status_field:
            return {'error': 'ステータスフィールドが見つかりません'}

        # 4. from_statusの確認
        if current_status != from_status:
            return {
                'error': f'現在のステータス "{current_status}" は期待される "{from_status}" と異なります',
                'current_status': current_status
            }

        # 5. to_statusのオプションIDを見つける
        field_id = status_field['id']
        to_option_id = None

        for option in status_field.get('options', []):
            if option['name'] == to_status:
                to_option_id = option['id']
                break

        if not to_option_id:
            available_statuses = [opt['name'] for opt in status_field.get('options', [])]
            return {
                'error': f'ステータス "{to_status}" が見つかりません',
                'available_statuses': available_statuses
            }

        # 6. ステータスを更新
        update_response = update_project_status(project_id, item_id, field_id, to_option_id)
        if 'errors' in update_response:
            return {'error': f'ステータス更新エラー: {update_response["errors"]}'}

        # 7. 成功レスポンス
        return {
            'success': True,
            'issue': {
                'number': issue_data['number'],
                'title': issue_data['title'],
                'node_id': issue_node_id
            },
            'project': {
                'id': project_id,
                'title': project_item['project']['title']
            },
            'status_change': {
                'from': from_status,
                'to': to_status
            },
            'update_response': update_response
        }

    except Exception as e:
        return {'error': f'処理中にエラーが発生しました: {str(e)}'}

def make_github_rest_request(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """GitHub REST APIにリクエストを送信"""
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise ValueError('GITHUB_TOKEN環境変数が設定されていません')

    url = f'https://api.github.com{endpoint}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8') if data else None,
        headers=headers,
        method=method
    )

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f'GitHub API Error: {e.code} - {error_body}')

def list_repository_issues(owner: str, repo: str, state: str = "open", labels: Optional[List[str]] = None, limit: int = 30) -> Dict[str, Any]:
    """
    リポジトリのissue一覧を取得します

    Args:
        owner: リポジトリオーナー（ユーザー名またはオーガニゼーション名）
        repo: リポジトリ名
        state: issueの状態（"open", "closed", "all"）デフォルト: "open"
        labels: フィルタするラベル名のリスト（省略可）
        limit: 取得するissue数の上限（デフォルト: 30）

    Returns:
        Issue一覧の情報
    """
    # GraphQLのFilterTypeを構築
    filter_conditions = []

    if state == "open":
        filter_conditions.append("is:open")
    elif state == "closed":
        filter_conditions.append("is:closed")
    # state == "all" の場合はフィルタ条件を追加しない

    if labels:
        for label in labels:
            filter_conditions.append(f'label:"{label}"')

    # 検索クエリを構築
    search_query = f'repo:{owner}/{repo} is:issue {" ".join(filter_conditions)}'

    query = """
    query($searchQuery: String!, $limit: Int!) {
      search(query: $searchQuery, type: ISSUE, first: $limit) {
        issueCount
        edges {
          node {
            ... on Issue {
              id
              number
              title
              state
              createdAt
              updatedAt
              author {
                login
              }
              labels(first: 10) {
                nodes {
                  name
                  color
                }
              }
              assignees(first: 5) {
                nodes {
                  login
                }
              }
              projectItems(first: 5) {
                nodes {
                  id
                  project {
                    id
                    title
                    number
                  }
                  fieldValues(first: 10) {
                    nodes {
                      ... on ProjectV2ItemFieldSingleSelectValue {
                        name
                        field {
                          ... on ProjectV2SingleSelectField {
                            name
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    variables = {
        'searchQuery': search_query,
        'limit': limit
    }

    return make_github_request(query, variables)

def update_issue_assignees(owner: str, repo: str, issue_number: int, assignees: List[str]) -> Dict[str, Any]:
    """
    Issue本文のassigneesフィールドを編集して担当エージェントを設定します

    Args:
        owner: リポジトリオーナー（ユーザー名またはオーガニゼーション名）
        repo: リポジトリ名
        issue_number: Issue番号
        assignees: 設定するassigneesのリスト（例: ["devplanner"] or ["bug-analysis"]）

    Returns:
        処理結果（成功/失敗の詳細情報）

    Note:
        TBD: 現在はIssue本文のassigneesフィールドを直接編集する方式だが、
        本文編集による意図しない変更のリスクがある。
        将来的にはラベルやカスタムフィールドなど本文を編集しない方式を検討する。
    """
    try:
        # 1. Issue本文を取得
        issue_response = make_github_rest_request('GET', f'/repos/{owner}/{repo}/issues/{issue_number}')
        if 'message' in issue_response and 'Not Found' in issue_response.get('message', ''):
            return {'error': f'Issue #{issue_number} が見つかりません'}

        current_body = issue_response.get('body', '')
        if not current_body:
            return {'error': 'Issue本文が空です'}

        # 2. assigneesフィールドを検索・置換
        # パターン: assignees: [] or assignees: [xxx] or assignees: [xxx, yyy]
        assignees_pattern = r'^assignees:\s*\[.*?\]'
        new_assignees_value = f'assignees: [{", ".join(assignees)}]'

        if re.search(assignees_pattern, current_body, re.MULTILINE):
            new_body = re.sub(assignees_pattern, new_assignees_value, current_body, flags=re.MULTILINE)
        else:
            return {
                'error': 'Issue本文にassigneesフィールドが見つかりません',
                'details': 'Issueテンプレートに "assignees: []" が含まれていることを確認してください'
            }

        # 3. Issue本文を更新
        update_response = make_github_rest_request(
            'PATCH',
            f'/repos/{owner}/{repo}/issues/{issue_number}',
            {'body': new_body}
        )

        # 4. 成功レスポンス
        return {
            'success': True,
            'issue_number': issue_number,
            'assignees': assignees,
            'updated_at': datetime.now().isoformat()
        }

    except Exception as e:
        return {'error': f'処理中にエラーが発生しました: {str(e)}'}

# MCPサーバーのインスタンスを作成
server = Server("github-mcp-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    MCPツールの一覧を返します
    """
    return [
        types.Tool(
            name="get_issue_project_info",
            description="Issueのプロジェクト情報とステータスを取得します",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_node_id": {"type": "string"}
                },
                "required": ["issue_node_id"]
            }
        ),
        types.Tool(
            name="update_project_status",
            description="GitHub Projects V2のアイテムのステータスを変更します",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "item_id": {"type": "string"},
                    "field_id": {"type": "string"},
                    "option_id": {"type": "string"}
                },
                "required": ["project_id", "item_id", "field_id", "option_id"]
            }
        ),
        types.Tool(
            name="get_issue_node_id_from_repo_info",
            description="リポジトリ情報からissueのNode IDを取得します",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "issue_number": {"type": "integer"}
                },
                "required": ["owner", "repo", "issue_number"]
            }
        ),
        types.Tool(
            name="change_issue_status_by_repo_info",
            description="リポジトリ情報を使ってissueのプロジェクトステータスを変更します(一連の処理を自動実行)",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "issue_number": {"type": "integer"},
                    "from_status": {"type": "string"},
                    "to_status": {"type": "string"}
                },
                "required": ["owner", "repo", "issue_number", "from_status", "to_status"]
            }
        ),
        types.Tool(
            name="change_issue_status_by_node_id",
            description="issueのNode IDを使ってプロジェクトステータスを変更します(一連の処理を自動実行)",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_node_id": {"type": "string"},
                    "from_status": {"type": "string"},
                    "to_status": {"type": "string"}
                },
                "required": ["issue_node_id", "from_status", "to_status"]
            }
        ),
        types.Tool(
            name="list_repository_issues",
            description="リポジトリのissue一覧を取得します",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "state": {
                        "type": "string",
                        "enum": ["open", "closed", "all"],
                        "default": "open"
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 30
                    }
                },
                "required": ["owner", "repo"]
            }
        ),
        types.Tool(
            name="update_issue_assignees",
            description="Issue本文のassigneesフィールドを編集して担当エージェントを設定します",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "issue_number": {"type": "integer"},
                    "assignees": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["owner", "repo", "issue_number", "assignees"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """
    ツールの呼び出しを処理します
    """
    try:
        if name == "get_issue_project_info":
            result = get_issue_project_info(arguments["issue_node_id"])
        elif name == "update_project_status":
            result = update_project_status(
                arguments["project_id"],
                arguments["item_id"],
                arguments["field_id"],
                arguments["option_id"]
            )
        elif name == "get_issue_node_id_from_repo_info":
            result = get_issue_node_id_from_repo_info(
                arguments["owner"],
                arguments["repo"],
                arguments["issue_number"]
            )
        elif name == "change_issue_status_by_repo_info":
            result = change_issue_status_by_repo_info(
                arguments["owner"],
                arguments["repo"],
                arguments["issue_number"],
                arguments["from_status"],
                arguments["to_status"]
            )
        elif name == "change_issue_status_by_node_id":
            result = change_issue_status_by_node_id(
                arguments["issue_node_id"],
                arguments["from_status"],
                arguments["to_status"]
            )
        elif name == "list_repository_issues":
            result = list_repository_issues(
                arguments["owner"],
                arguments["repo"],
                arguments.get("state", "open"),
                arguments.get("labels"),
                arguments.get("limit", 30)
            )
        elif name == "update_issue_assignees":
            result = update_issue_assignees(
                arguments["owner"],
                arguments["repo"],
                arguments["issue_number"],
                arguments["assignees"]
            )
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    # Serve the server using stdio
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="github-mcp-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())