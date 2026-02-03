# Estoque Casa de Eventos (Backend)

Stack:
- FastAPI
- SQLAlchemy 2.0
- Alembic
- Postgres (Docker)

## Subir o projeto
1. Copie `.env.example` para `.env` e ajuste se quiser.
2. Rode:
```bash
docker compose up --build
```
A API sobe em `http://localhost:8000` e o Swagger em `http://localhost:8000/docs`.

> O container da API executa `alembic upgrade head` automaticamente ao subir.

## Criar/atualizar migrations
Dentro do container da API:
```bash
docker exec -it estoque_eventos_api bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```
