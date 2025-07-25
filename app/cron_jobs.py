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


sql_store = CustomSQLAlchemyJobStore(engine=engine)

# Initialize an AsyncIOScheduler with the jobstore
scheduler = AsyncIOScheduler(
    jobstores={"default": sql_store},
    timezone=ZoneInfo("Africa/Algiers"),
)


def scheduled_job_1(msg: str):
    print(msg)


def scheduled_job_2():
    print("scheduled_job_2")


def scheduled_job_3():
    print("scheduled_job_3")


job_1 = scheduler.add_job(
    func=scheduled_job_1,
    args=["periodic 10 min job"],
    id="interval_job_1",
    trigger="interval",
    minutes=10,
    replace_existing=True,
)
# job_2 = scheduler.add_job(
#     func=scheduled_job_2,
#     id="date_job_2",
#     trigger="date",
#     run_date="2025-07-22 14:50:10",
#     replace_existing=True,
# )
# job_3 = scheduler.add_job(
#     func=scheduled_job_3,
#     id="cron_job_3",
#     trigger="cron",
#     day_of_week="mon-sun",
#     hour=14,
#     minute=50,
#     replace_existing=True,
# )
