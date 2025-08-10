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




async def run_matching_job():
    """Run the matching algorithm for all users"""
    from app.services.matching_cron_service import MatchingCronService
    
    try:
        matching_service = MatchingCronService()
        result = await matching_service.run_daily_matching()
        print(f"🎯 MATCHING JOB COMPLETED: {result['new_matches_created']} new matches created")
    except Exception as e:
        print(f"❌ MATCHING JOB ERROR: {str(e)}")



# Matching job - runs every 10 minutes
matching_job = scheduler.add_job(
    func=run_matching_job,
    id="matching_job_10min",
    trigger="interval",
    minutes=10,
    replace_existing=True,
)

