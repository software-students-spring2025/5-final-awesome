# Final Project

An exercise to put to practice software development teamwork, subsystem communication, containers, deployment, and CI/CD pipelines. See [instructions](./instructions.md) for details.

## Team members
- [Tony Zhao](https://github.com/Tonyzsp)
- [Rin Qi](https://github.com/Rin-Qi)
- [Corrine Huang](https://github.com/ChuqiaoHuang)
- [Johnny Ding](https://github.com/yd2960)

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