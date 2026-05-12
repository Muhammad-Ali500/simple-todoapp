import os
import json
import redis.asyncio as redis
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import engine, get_db, Base
from app.models import Todo
from app.schemas import TodoCreate, TodoUpdate

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = FastAPI(title="Todo App")

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

redis_client: redis.Redis | None = None


@app.on_event("startup")
async def startup():
    global redis_client
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
    except Exception as e:
        print(f"Redis connection failed: {e}")
        redis_client = None


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/health")
async def health():
    redis_ok = False
    if redis_client:
        try:
            await redis_client.ping()
            redis_ok = True
        except Exception:
            pass
    return {
        "status": "ok",
        "redis_connected": redis_ok,
    }


@app.get("/api/todos", response_model=list[dict])
async def list_todos(db: Session = Depends(get_db)):
    todos = db.query(Todo).order_by(Todo.created_at.desc()).all()
    cached_count = None
    if redis_client:
        try:
            cached_count = await redis_client.get("todo:count")
        except Exception:
            pass
    result = []
    for t in todos:
        result.append({
            "id": t.id,
            "title": t.title,
            "description": t.description or "",
            "completed": t.completed,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })
    return result


@app.get("/api/todos/{todo_id}", response_model=dict)
async def get_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {
        "id": todo.id,
        "title": todo.title,
        "description": todo.description or "",
        "completed": todo.completed,
        "created_at": todo.created_at.isoformat() if todo.created_at else None,
    }


@app.post("/api/todos", response_model=dict, status_code=201)
async def create_todo(payload: TodoCreate, db: Session = Depends(get_db)):
    todo = Todo(title=payload.title, description=payload.description or "")
    db.add(todo)
    db.commit()
    db.refresh(todo)
    if redis_client:
        try:
            count = db.query(Todo).count()
            await redis_client.set("todo:count", count)
        except Exception:
            pass
    return {
        "id": todo.id,
        "title": todo.title,
        "description": todo.description or "",
        "completed": todo.completed,
        "created_at": todo.created_at.isoformat() if todo.created_at else None,
    }


@app.put("/api/todos/{todo_id}", response_model=dict)
async def update_todo(todo_id: int, payload: TodoUpdate, db: Session = Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if payload.title is not None:
        todo.title = payload.title
    if payload.description is not None:
        todo.description = payload.description
    if payload.completed is not None:
        todo.completed = payload.completed
    db.commit()
    db.refresh(todo)
    return {
        "id": todo.id,
        "title": todo.title,
        "description": todo.description or "",
        "completed": todo.completed,
        "created_at": todo.created_at.isoformat() if todo.created_at else None,
    }


@app.delete("/api/todos/{todo_id}", status_code=204)
async def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo)
    db.commit()
    if redis_client:
        try:
            count = db.query(Todo).count()
            await redis_client.set("todo:count", count)
        except Exception:
            pass
    return None


@app.get("/api/stats")
async def stats(db: Session = Depends(get_db)):
    total = db.query(Todo).count()
    completed = db.query(Todo).filter(Todo.completed == True).count()
    stats_data = {"total": total, "completed": completed, "pending": total - completed}
    if redis_client:
        try:
            cached = await redis_client.get("todo:count")
            stats_data["cached_count"] = int(cached) if cached else None
        except Exception:
            pass
    return stats_data
