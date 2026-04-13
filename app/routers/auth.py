from fastapi import APIRouter, HTTPException, Depends, Request, Response, Form
from sqlmodel import select
from app.database import SessionDep
from app.models import *
from app.utilities import flash
from app.auth import encrypt_password, verify_password, create_access_token, AuthDep
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import status
from . import templates
from fastapi.responses import HTMLResponse, RedirectResponse

auth_router = APIRouter(tags=["Authentication"])

@auth_router.post("/login")
async def login_action(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SessionDep,
    request: Request
) -> Response:
    user = db.exec(select(User).where(User.username == form_data.username)).one_or_none()
    if not user or not verify_password(form_data.password, user.password):
        flash(request, "Invalid username or password", "error")
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    response = RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@auth_router.post('/signup', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup_user(request:Request, db:SessionDep, username: Annotated[str, Form()], email: Annotated[str, Form()], password: Annotated[str, Form()],):
    existing_user = db.exec(select(User).where((User.username == username) | (User.email == email))).first()
    if existing_user:
        flash(request, "Username or email already exists", "error")
        return RedirectResponse(url="/signup", status_code=status.HTTP_303_SEE_OTHER)
    
    new_user = User(
        username=username,
        email=email,
        password=encrypt_password(password),
        role="regular_user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    flash(request, "Account created successfully! Please login.", "success")
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@auth_router.get("/identify", response_model=UserResponse)
def get_user_by_id(db: SessionDep, user:AuthDep):
    return user

@auth_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="login.html",
    )

@auth_router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="signup.html",
    )

@auth_router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    flash(request, "You have been logged out", "success")
    return response