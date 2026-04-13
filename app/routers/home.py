from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import select
from app.database import SessionDep
from app.models import *
from app.auth import AuthDep, IsUserLoggedIn
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import status
from . import templates

home_router = APIRouter()

@home_router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    user_logged_in: IsUserLoggedIn
):
    if user_logged_in:
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@home_router.get("/app", response_class=HTMLResponse)
async def app_dashboard(
    request: Request,
    user: AuthDep
):
    return templates.TemplateResponse(
        request=request,
        name="todo.html",
        context={
            "current_user": user,
            "todos": user.todos
        }
    )