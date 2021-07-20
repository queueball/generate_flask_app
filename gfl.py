#!/usr/local/bin/python3
import os
import pathlib
import random
import subprocess
import socket

import click
import yaml


VALUES = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def generate_folders(output: str, module: str):
    folders = [
        (output,),
        (output, module, "app"),
        (output, module, "app", "static"),
        (output, module, "app", "templates"),
        (output, module, "tests"),
        (output, "caches"),
    ]
    for folder in folders:
        path = os.path.join(*folder)
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        print("adding:", path)


def generate_myapp(output: str, module: str):
    path = os.path.join(output, module, "app", "myapp.py")
    with open(path, "w+") as f:
        print("adding:", path)
        f.write(
            """import eventlet

eventlet.monkey_patch()

import datetime
import json
import logging
import os

import flask
import flask_socketio
import retry


logging.basicConfig(level=logging.INFO)
app = flask.Flask(__name__)

BASE = os.environ.get("BASE", "")
SOCKET_ROUTE = os.environ.get("SOCKET_ROUTE", "")
SOCKETIO_PATH = ("/" if SOCKET_ROUTE else "") + SOCKET_ROUTE + "/socket.io"

logging.info(SOCKETIO_PATH)


def get_socketio(message_queue):
    if message_queue:
        # This is needed because the test socketio client doesn't accept message_queue as a parameter
        return flask_socketio.SocketIO(
            app,
            path=SOCKETIO_PATH,
            message_queue=f"amqp://guest:guest@rabbitmq:5672/{BASE}",
            async_mode="eventlet",
        )
    else:
        return flask_socketio.SocketIO(app, path=SOCKETIO_PATH, async_mode="eventlet")


socketio = get_socketio(True)


@app.route("/")
def handle_root():
    try:
        data = []
    except:
        data = []
    return flask.render_template(
        "index.html",
        data=json.dumps(data),
        base=BASE,
        socketio_path=SOCKETIO_PATH,
    )


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", debug=True)"""
        )


def generate_tests(output: str, module: str):
    path = os.path.join(output, module, "conftest.py")
    with open(path, "w+") as f:
        print("adding:", path)
    path = os.path.join(output, module, "tests", "test_myapp.py")
    with open(path, "w+") as f:
        print("adding:", path)
        f.write(
            """from app import myapp


def test_1():
    flask_test_client = myapp.app.test_client()
    socketio_test_client = myapp.get_socketio(False).test_client(myapp.app, flask_test_client=flask_test_client)

    assert socketio_test_client.is_connected()"""
        )


def generate_common_css(output: str, module: str):
    path = os.path.join(output, module, "app", "static", "common.css")
    with open(path, "w+"):
        print("adding:", path)
        pass


def generate_common_js(output: str, module: str):
    path = os.path.join(output, module, "app", "static", "common.js")
    with open(path, "w+") as f:
        print("adding:", path)
        f.write(
            """"use strict";
var COMMON = COMMON || (function() {
  return {
    init: function(args) {
      let data = args.data;
      let socket = io({path: args.socketio_path});
      socket.on('connect', () => {});
      socket.on('disconnect', () => {});
      socket.on('reload', () => {});

      let app = new Vue({
        el: '#app',
        data: {
        },
      });
    },
  };
}());
"""
        )


def generate_index(output: str, module: str):
    path = os.path.join(output, module, "app", "templates", "index.html")
    with open(path, "w+") as f:
        print("adding:", path)
        f.write(
            """<!doctype html>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<html>
  <head>
    <link rel="icon" href="data:,">
    <link rel="stylesheet" href="/{{ base }}/static/common.css">
    <title>"""
            + module.title()
            + """</title>
  </head>
  <body>
    <div id="app">
        Hello World
    </div>
  </body>
  <footer>
    <script src="https://cdn.jsdelivr.net/npm/socket.io-client@4/dist/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/vue/dist/vue.js"></script>
    <script src="/{{ base }}/static/common.js"></script>
    <script>
      COMMON.init({
        data: {{ data | safe }},
        socketio_path: "{{ socketio_path }}",
      });
    </script>
  </footer>
</html>"""
        )


def generate_requirements(output: str, module: str):
    path = os.path.join(output, module, "requirements.txt")
    with open(path, "w+") as f:
        print("adding:", path)
        f.write(
            """### flask-socketio ## this covers all of flask
Flask-SocketIO==5.0.1
Flask==1.1.2
Jinja2==2.11.3
MarkupSafe==1.1.1
Werkzeug==1.0.1
bidict==0.21.2
click==7.1.2
itsdangerous==1.1.0
python-engineio==4.1.0
python-socketio==5.2.1

### Kombu ## needed to pytest... flask-socketio
amqp==5.0.6
kombu==5.0.2
vine==5.0.0

### eventlet
dnspython==1.16.0
eventlet==0.30.2
greenlet==1.0.0
six==1.15.0

### flask_rabmq
# Flask==1.1.2
# Jinja2==2.11.3
# MarkupSafe==1.1.1
# Werkzeug==1.0.1
# amqp==5.0.6
# click==7.1.2
flask_rabmq==0.0.19
# itsdangerous==1.1.0
# kombu==5.0.2
# vine==5.0.0

### retry
decorator==5.0.7
py==1.10.0
retry==0.9.2

### pytest
attrs==20.3.0
iniconfig==1.1.1
packaging==20.9
pluggy==0.13.1
py==1.10.0
pyparsing==2.4.7
pytest==6.2.3
toml==0.10.2
"""
        )


def generate_setup_cfg(output: str, module: str):
    path = os.path.join(output, module, "setup.cfg")
    with open(path, "w+") as f:
        print("adding:", path)
        f.write(
            """[flake8]
extend-ignore = W503, E203"""
        )


def generate_dockerfile(output: str, module: str):
    path = os.path.join(output, module, "dockerfile")
    with open(path, "w+") as f:
        print("adding:", path)
        f.write(
            """FROM python:slim-buster
COPY requirements.txt requirements.txt
RUN apt-get update \\
    && apt-get install -y gcc libssl-dev \\
    && pip install --upgrade pip \\
    && pip install -r requirements.txt \\
    && mkdir -p /app/caches
COPY . /app
WORKDIR /app
STOPSIGNAL SIGINT
CMD ["python", "app/myapp.py"]
"""
        )


def generate_docker_compose(output: str, module: str, host: str, port: str):
    path = os.path.join(output, "docker-compose.yml")
    with open(path, "w+") as f:
        print("adding:", path)
        yaml.dump(
            {
                "version": "2",
                "services": {
                    module: {
                        "build": module,
                        "ports": [f"{port}:5000"],
                        "restart": "unless-stopped",
                        "volumes": [
                            ".caches/:/app/caches",
                        ],
                        "environment": [
                            "REVERSE_PROXY=true",
                            f"HOST={host}:{port}",
                            f"BASE={module}",
                            f'SOCKET_ROUTE={"".join(random.choices(VALUES, k=5))}',
                        ],
                    },
                },
            },
            f,
            sort_keys=False,
        )


def generate_git(output: str, module: str):
    subprocess.Popen(["git", "init"], cwd=output).wait()
    subprocess.Popen(["git", "add", "-v", "."], cwd=output).wait()
    subprocess.Popen(
        ["git", "commit", "-m", '"Added: initial commit"'], cwd=output
    ).wait()


@click.command()
@click.option("-o", "--output", required=True, help="Output path")
@click.option("-m", "--module", required=True)
@click.option("--host", default=socket.gethostname())
@click.option("--port", default="8080")
def controller(output: str, module: str, host: str, port: str):
    generate_folders(output, module)
    generate_myapp(output, module)
    generate_tests(output, module)
    generate_dockerfile(output, module)
    generate_docker_compose(output, module, host, port)
    generate_requirements(output, module)
    generate_index(output, module)
    generate_common_js(output, module)
    generate_common_css(output, module)
    generate_git(output, module)


if __name__ == "__main__":
    controller()
