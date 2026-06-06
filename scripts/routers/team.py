"""团队 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.team import TeamService

router = APIRouter()
service = TeamService()


class CreateTeamRequest(BaseModel):
    name: str
    owner_id: str


class InviteRequest(BaseModel):
    team_id: str
    email: str
    role: str = "member"


class AcceptRequest(BaseModel):
    token: str
    user_id: str


@router.post("/create")
async def create_team(req: CreateTeamRequest):
    """创建团队"""
    return service.create_team(req.name, req.owner_id)


@router.post("/invite")
async def invite_member(req: InviteRequest):
    """邀请成员"""
    return service.invite_member(req.team_id, req.email, req.role)


@router.post("/accept")
async def accept_invitation(req: AcceptRequest):
    """接受邀请"""
    result = service.accept_invitation(req.token, req.user_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/user/{user_id}")
async def list_user_teams(user_id: str):
    """列出用户的团队"""
    return service.list_user_teams(user_id)


@router.get("/{team_id}")
async def get_team(team_id: str):
    """获取团队详情"""
    team = service.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    return team
