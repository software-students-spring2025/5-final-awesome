# Final Project

An exercise to put to practice software development teamwork, subsystem communication, containers, deployment, and CI/CD pipelines. See [instructions](./instructions.md) for details.

## Development Environment Setup
Boot your docker app\
Orchestrate the containers using

```
docker compose up --build
```

The web app now runs on [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Install and Run Formatter

```
cd web-app

python -m venv venv
source venv/bin/activate

python -m install -r requirements.txt
python -m black .
```