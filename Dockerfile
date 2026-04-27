FROM python:3.11-slim

WORKDIR /root/todo-app

COPY app.py todos.db ./

RUN pip install flask

EXPOSE 3434

CMD ["python", "app.py"]
