![CI](https://github.com/software-students-spring2025/5-final-awesome/actions/workflows/test.yml/badge.svg)
![CD](https://github.com/software-students-spring2025/5-final-awesome/actions/workflows/deploy.yml/badge.svg)

# Easy Anonymous Polls

This project allows users to create polls and vote on those polls. A poll code will be automatically generated once a poll is created. Guests can use the poll code to enter the voting page and vote. A result page is also included to show the result of the poll. Log in and sign up features are optional for users who wants to keep track of their polls.\
Production server with gunicorn is on [http://45.55.55.183:8000/](http://45.55.55.183:8000/).

## Team members

- [Tony Zhao](https://github.com/Tonyzsp)
- [Rin Qi](https://github.com/Rin-Qi)
- [Corrine Huang](https://github.com/ChuqiaoHuang)
- [Johnny Ding](https://github.com/yd2960)

## Docker Hub Images

- [Web app image](https://hub.docker.com/repository/docker/yd2960/project-5-team-awesome/tags/latest/sha256-a0da42c6182e949fb3cad374a3dba9f22b7249fefd09ea0f6b80ba587344b347)
- [Official Mongodb Image](https://hub.docker.com/_/mongo)

## Development Environment Setup

Boot your docker app\
Orchestrate the containers using

```
docker compose up --build
```

The web app now runs on [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Environment Variables Setup

Look at [web-app/example.env](web-app/example.env)\
Simply rename the file to `.env` and change the value of `SECRET_KEY` as you like

## Install and Run Formatter

```
cd web-app

python -m venv venv
source venv/bin/activate

python -m install -r requirements.txt
python -m black .
```

## Acknowledgements

This project leverages [Dice Bear API](https://www.dicebear.com/), especially [bottts-neutral](https://bottts.com/) created by [Pablo Stanley](https://x.com/pablostanley).
