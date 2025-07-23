import pickle
from zoneinfo import ZoneInfo

from apscheduler.jobstores.sqlalchemy import BaseJobStore, SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.database import engine
from app.models import APSchedulerJob


class CustomSQLAlchemyJobStore(SQLAlchemyJobStore):
    def __init__(self, engine):
        self.engine = engine
        self.pickle_protocol = pickle.HIGHEST_PROTOCOL
        self.jobs_t = APSchedulerJob.__table__

    def start(self, scheduler, alias):
        return BaseJobStore.start(self, scheduler, alias)


# Initialize a SQLAlchemyJobStore with SQLite database
jobstores = {
    "default": CustomSQLAlchemyJobStore(engine=engine),
}

# Initialize an AsyncIOScheduler with the jobstore
scheduler = AsyncIOScheduler(jobstores=jobstores, timezone=ZoneInfo("Africa/Algiers"))


@scheduler.scheduled_job(trigger="interval", seconds=50, id="interval_job_1")
def scheduled_job_1():
    print("scheduled_job_1")


@scheduler.scheduled_job(trigger="date", run_date="2025-07-22 14:50:10", id="date_job_2")
def scheduled_job_2():
    print("scheduled_job_2")


@scheduler.scheduled_job(
    trigger="cron",
    day_of_week="mon-sun",
    hour=14,
    minute=50,
    id="cron_job_3",
)
def scheduled_job_3():
    print("scheduled_job_3")
