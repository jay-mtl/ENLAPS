from invoke import Collection, Task

from tasks.db import db

app_path = "api"
tests_path = "tests"


@Task
def test(ctx):
    ctx.run(
        f"py.test -v --cov-config=.coveragerc --cov={app_path} --cov-report=term-missing {tests_path}",
        pty=True,
    )


@Task
def safety(ctx):
    ctx.run("safety scan --ignore=40291")


@Task
def lint(ctx):
    ctx.run(f"flake8 {app_path} {tests_path}")


@Task
def static_check(ctx):
    ctx.run(f"mypy --strict {app_path}", pty=True)


@Task
def reformat(ctx):
    ctx.run("black .", pty=True)


ns = Collection()
ns.add_task(test)
ns.add_task(safety)
ns.add_task(lint)
ns.add_task(static_check)
ns.add_task(reformat)
ns.add_collection(db)
