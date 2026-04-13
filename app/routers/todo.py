from fastapi import APIRouter, HTTPException, Depends, Request, Response, Form
from sqlmodel import select
from app.database import SessionDep
from app.models import *
from app.auth import encrypt_password, verify_password, create_access_token, AuthDep
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import status
from fastapi.responses import HTMLResponse, RedirectResponse
from app.utilities import flash
from . import templates


todo_router = APIRouter(tags=["Todo Management"])

@todo_router.post("/todos")
def create_todo_action(request: Request, text: Annotated[str, Form()], db:SessionDep, user:AuthDep):
    if not text or text.strip() == "":
        flash(request, "Todo text cannot be empty", "error")
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    
    new_todo = Todo(text=text.strip(), user_id=user.id)
    try:
        db.add(new_todo)
        db.commit()
        flash(request, "Todo created successfully", "success")
    except Exception:
        db.rollback()
        flash(request, "An error occurred while creating the todo", "error")
    
    return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)

@todo_router.post('/toggle/{id}')
async def toggle_todo_action(request: Request, id: int, db:SessionDep, user:AuthDep):
    todo = db.exec(select(Todo).where(Todo.id == id, Todo.user_id == user.id)).one_or_none()
    if not todo:
        flash(request, "Todo not found or unauthorized", "error")
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    
    todo.done = not todo.done
    try:
        db.add(todo)
        db.commit()
        flash(request, f"Todo '{todo.text}' updated", "success")
    except Exception:
        db.rollback()
        flash(request, "An error occurred while updating the todo", "error")
    
    return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)

@todo_router.post('/editTodo/{id}')
def edit_todo_action(request: Request, id: int, text: Annotated[str, Form()], db:SessionDep, user:AuthDep):
    todo = db.exec(select(Todo).where(Todo.id == id, Todo.user_id == user.id)).one_or_none()
    if not todo:
        flash(request, "Todo not found or unauthorized", "error")
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    
    if not text or text.strip() == "":
        flash(request, "Todo text cannot be empty", "error")
        return RedirectResponse(url=f"/editTodo/{id}", status_code=status.HTTP_303_SEE_OTHER)
    
    todo.text = text.strip()
    try:
        db.add(todo)
        db.commit()
        flash(request, "Todo updated successfully", "success")
    except Exception:
        db.rollback()
        flash(request, "An error occurred while updating the todo", "error")
    
    return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)

@todo_router.get('/deleteTodo/{id}')
def delete_todo_action(request: Request, id: int, db:SessionDep, user:AuthDep):
    todo = db.exec(select(Todo).where(Todo.id == id, Todo.user_id == user.id)).one_or_none()
    if not todo:
        flash(request, "Todo not found or unauthorized", "error")
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    
    todo_text = todo.text
    try:
        db.delete(todo)
        db.commit()
        flash(request, f"Todo '{todo_text}' deleted successfully", "success")
    except Exception:
        db.rollback()
        flash(request, "An error occurred while deleting the todo", "error")
    
    return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)

@todo_router.get('/editTodo/{id}')
def edit_todo_page(request: Request, id: int, db:SessionDep, user:AuthDep):
    todo = db.exec(select(Todo).where(Todo.id == id, Todo.user_id == user.id)).one_or_none()
    todos = []

    if not todo:
        flash(request, 'Invalid id or unauthorized')
    else:
        todos = user.todos
    
    return templates.TemplateResponse(
        request=request, 
        name="edit.html",
        context={
            "current_user": user,
            "todo": todo,
            "todos": todos
        }
    )

# ============ EXERCISE 2: Category Management ============

@todo_router.post('/category')
def create_category_action(request: Request, name: Annotated[str, Form()], db: SessionDep, user: AuthDep):
    if not name or name.strip() == "":
        flash(request, "Category name cannot be empty", "error")
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    
    existing_category = db.exec(select(Category).where(Category.text == name.strip(), Category.user_id == user.id)).first()
    if existing_category:
        flash(request, "Category already exists", "error")
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    
    new_category = Category(text=name.strip(), user_id=user.id)
    try:
        db.add(new_category)
        db.commit()
        flash(request, f"Category '{name}' created successfully", "success")
    except Exception:
        db.rollback()
        flash(request, "An error occurred while creating the category", "error")
    
    return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)

@todo_router.post('/todo/{todo_id}/category/{cat_id}')
def add_category_to_todo_action(request: Request, todo_id: int, cat_id: int, db: SessionDep, user: AuthDep):
    todo = db.exec(select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id)).one_or_none()
    if not todo:
        flash(request, "Todo not found or unauthorized", "error")
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    
    category = db.exec(select(Category).where(Category.id == cat_id, Category.user_id == user.id)).one_or_none()
    if not category:
        flash(request, "Category not found or unauthorized", "error")
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    
    if category in todo.categories:
        flash(request, "Category already assigned to this todo", "error")
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    
    todo.categories.append(category)
    try:
        db.add(todo)
        db.commit()
        flash(request, f"Category '{category.text}' added to todo '{todo.text}'", "success")
    except Exception:
        db.rollback()
        flash(request, "An error occurred while adding category to todo", "error")
    
    return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)

@todo_router.get('/todo/{todo_id}/category/{cat_id}/remove')
def remove_category_from_todo_action(request: Request, todo_id: int, cat_id: int, db: SessionDep, user: AuthDep):
    todo = db.exec(select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id)).one_or_none()
    if not todo:
        flash(request, "Todo not found or unauthorized", "error")
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    
    category = db.exec(select(Category).where(Category.id == cat_id, Category.user_id == user.id)).one_or_none()
    if not category:
        flash(request, "Category not found or unauthorized", "error")
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    
    if category not in todo.categories:
        flash(request, "Category is not assigned to this todo", "error")
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    
    todo.categories.remove(category)
    try:
        db.add(todo)
        db.commit()
        flash(request, f"Category '{category.text}' removed from todo '{todo.text}'", "success")
    except Exception:
        db.rollback()
        flash(request, "An error occurred while removing category from todo", "error")
    
    return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)

# ============ EXERCISE 3: Category Filtering ============

@todo_router.get('/category/{cat_id}')
def view_category_todos(request: Request, cat_id: int, db: SessionDep, user: AuthDep):
    category = db.exec(select(Category).where(Category.id == cat_id, Category.user_id == user.id)).one_or_none()
    if not category:
        flash(request, "Category not found or unauthorized", "error")
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse(
        request=request,
        name="category.html",
        context={
            "current_user": user,
            "category": category,
            "todos": category.todos
        }
    )