from invoke import Collection, Task
from alembic import command
from alembic.config import Config


config = Config("alembic.ini")


@Task
def migrate(ctx, message, revision):
    command.revision(config, message=message, rev_id=revision, autogenerate=True)


@Task
def upgrade(ctx, revision="head"):
    command.upgrade(config, revision=revision)


@Task
def downgrade(ctx, revision="-1"):
    command.downgrade(config, revision=revision)


db = Collection("db")
db.add_task(migrate)
db.add_task(upgrade)
db.add_task(downgrade)
