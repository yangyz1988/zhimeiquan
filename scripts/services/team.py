"""团队协作服务 - 多用户工作区"""

import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from services.logging import logger


class TeamService:
    """团队协作服务"""

    def __init__(self, data_dir: str = "../data/teams"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.teams_file = self.data_dir / "teams.json"
        self.invitations_file = self.data_dir / "invitations.json"

    def _load_teams(self) -> list[dict]:
        if not self.teams_file.exists():
            return []
        with open(self.teams_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_teams(self, teams: list[dict]):
        with open(self.teams_file, "w", encoding="utf-8") as f:
            json.dump(teams, f, ensure_ascii=False, indent=2)

    def _load_invitations(self) -> list[dict]:
        if not self.invitations_file.exists():
            return []
        with open(self.invitations_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_invitations(self, invitations: list[dict]):
        with open(self.invitations_file, "w", encoding="utf-8") as f:
            json.dump(invitations, f, ensure_ascii=False, indent=2)

    def create_team(self, name: str, owner_id: str) -> dict:
        """创建团队"""
        team = {
            "team_id": f"team_{secrets.token_hex(8)}",
            "name": name,
            "owner_id": owner_id,
            "members": [
                {
                    "user_id": owner_id,
                    "role": "owner",
                    "joined_at": datetime.now().isoformat(),
                }
            ],
            "plan": "team",
            "created_at": datetime.now().isoformat(),
        }

        teams = self._load_teams()
        teams.append(team)
        self._save_teams(teams)

        logger.info(f"团队已创建: {name}", team_id=team["team_id"])
        return team

    def invite_member(self, team_id: str, email: str, role: str = "member") -> dict:
        """邀请成员加入团队"""
        token = secrets.token_urlsafe(32)
        invitation = {
            "invitation_id": f"inv_{secrets.token_hex(8)}",
            "team_id": team_id,
            "email": email,
            "role": role,
            "token": token,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        }

        invitations = self._load_invitations()
        invitations.append(invitation)
        self._save_invitations(invitations)

        logger.info(f"已邀请: {email} -> {team_id}")
        return invitation

    def accept_invitation(self, token: str, user_id: str) -> dict:
        """接受邀请"""
        invitations = self._load_invitations()
        invitation = next((i for i in invitations if i["token"] == token), None)
        if not invitation:
            return {"error": "邀请无效"}
        if invitation["status"] != "pending":
            return {"error": "邀请已被使用"}
        if datetime.fromisoformat(invitation["expires_at"]) < datetime.now(timezone.utc):
            return {"error": "邀请已过期"}

        # 添加成员到团队
        teams = self._load_teams()
        team = next((t for t in teams if t["team_id"] == invitation["team_id"]), None)
        if not team:
            return {"error": "团队不存在"}

        team["members"].append(
            {
                "user_id": user_id,
                "role": invitation["role"],
                "joined_at": datetime.now().isoformat(),
            }
        )

        # 更新邀请状态
        invitation["status"] = "accepted"
        invitation["accepted_at"] = datetime.now().isoformat()

        self._save_teams(teams)
        self._save_invitations(invitations)

        logger.info(f"{user_id} 加入了 {invitation['team_id']}")
        return team

    def get_team(self, team_id: str) -> dict | None:
        """获取团队详情"""
        teams = self._load_teams()
        return next((t for t in teams if t["team_id"] == team_id), None)

    def list_user_teams(self, user_id: str) -> list[dict]:
        """列出用户所在的所有团队"""
        teams = self._load_teams()
        return [t for t in teams if any(m["user_id"] == user_id for m in t["members"])]

    def share_project(self, team_id: str, project_id: str, shared_by: str) -> dict:
        """分享项目到团队"""
        share = {
            "share_id": f"share_{secrets.token_hex(8)}",
            "team_id": team_id,
            "project_id": project_id,
            "shared_by": shared_by,
            "shared_at": datetime.now().isoformat(),
            "permissions": ["view", "comment", "edit"],
        }

        share_file = self.data_dir / "shares.json"
        shares = []
        if share_file.exists():
            with open(share_file, "r", encoding="utf-8") as f:
                shares = json.load(f)
        shares.append(share)
        with open(share_file, "w", encoding="utf-8") as f:
            json.dump(shares, f, ensure_ascii=False, indent=2)

        return share
