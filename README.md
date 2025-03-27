# ENLAPS Pictures Storage Service

The role of this service is to store picures form Tikee cameras.

## Configuration

This micro-service is configurable through environement variables.
The following configuration is available:
|   Variable   |                       Format                        |                         Default                          | Description                   |
| :----------: | :-------------------------------------------------: | :------------------------------------------------------: | ----------------------------- |
| ENVIRONMENT  | {`development`, `testing`, `staging`, `production`} |                       `production`                       | App run-time environment name |
|    DEBUG     |                  {`true`, `false`}                  |                         `false`                          | Debug variable                |
| DATABASE_URL |                        `str`                        | `postgresql+asyncpg://test:test@localhost/tikeePictures` |                               |

## Docker

### Build

`docker build -t ENLAPS/fastapi-app:latest .`

### Run

We need to run a posrtgesql instance, the easiest way is to use docker, but we need to create a common network, that way the database and the service can communicate easily.

```bash
# Create a network
docker network create --driver bridge fastapi-net

# Create a postgresql instance
docker run -d --name fastapi-pgl \
    --network fastapi-net \
    -e POSTGRESQL_USERNAME=test \
    -e POSTGRESQL_PASSWORD=test \
    -e POSTGRESQL_DATABASE=tikeePictures \
    -p 5432:5432 bitnami/postgresql:16

```

We can now lauch the fast-api application

```bash
    docker run --name fastapi-app \
        --network fastapi-net \
        -e DATABASE_URL=postgresql+asyncpg://test:test@fastapi-pgl/tikeePictures \
        -p 8000:80 ENLAPS/fastapi-app:latest
```

## Usage

You can now go on `http://localhost/docs`.

## Development

You need to have `uv` install on your machine, or install it with 

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

1. Install dependencies

```bash
    uv sync
```

2. Run the service:

```bash
uvicorn app.app:app
```

### VScode

Use the following `.vscode/launch.json` config:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python Debugger: ENLAPS",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": ["app.app:app","--reload"]
        }
    ]
}
```

### Actions

- Run the tests: `inv test`
- Reformat the code: `inv reformat`
- Check code linting: `inv lint`
- Check static typing: `inv static-check`

Note that for the test, when we launch the docker postgresql instance, we need to create the database test

```bash
psql -U username -h localhost postgres
create database "tikeePictures_test";
```

### Migration

For the migration, 

```bash
inv db.migrate "messages" revision_id
```

and to upgrade

```bash
inv db.upgrade
```

## Scalability

For the scalibility, we put only 1 worker in the `Dockerfile`, but the easiest way will be for example to put this `Deployment`, `Service` and `HorizontalPodAutoscaler`, in a Kubernetes cluster

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
spec:
  selector:
    matchLabels:
      run: fastapi-app
  template:
    metadata:
      labels:
        run: fastapi-app
    spec:
      containers:
      - name: fastapi-app
        image: ENLAPS/fastapi-app
        ports:
        - containerPort: 80
        resources:
          limits:
            cpu: 500m
          requests:
            cpu: 200m
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-app
  labels:
    run: fastapi-app
spec:
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  selector:
    run: fastapi-app
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-app
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
```

