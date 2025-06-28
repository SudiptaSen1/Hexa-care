from fastapi import APIRouter
from models.user_model import UserCreate, UserLogin, UserResponse
from controllers.auth_controller import signup, signin, get_user_by_id

router = APIRouter()

@router.post("/signup", response_model=UserResponse)
async def register_user(user: UserCreate):
    return await signup(user)

@router.post("/signin", response_model=UserResponse)
async def login_user(user: UserLogin):
    return await signin(user)

# @router.get("/user/{user_id}", response_model=UserResponse)
# async def get_user(user_id: str = Path(..., description="MongoDB user _id")):
#     return await get_user_by_id(user_id)