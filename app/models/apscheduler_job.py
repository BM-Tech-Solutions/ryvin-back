from sqlalchemy import Float, LargeBinary, Unicode
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class APSchedulerJob(Base):
    """
    Explicit table definition for APScheduler jobs
    """

    __tablename__ = "apscheduler_jobs"

    id: Mapped[str] = mapped_column(Unicode(191), primary_key=True)
    next_run_time: Mapped[float] = mapped_column(Float(25), index=True)
    job_state: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
