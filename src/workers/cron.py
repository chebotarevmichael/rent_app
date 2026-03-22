import dramatiq
from periodiq import cron  # type: ignore[import-untyped]

from src.scripts.cron import cron_generate_out_events


@dramatiq.actor(periodic=cron('* * * * *'), queue_name='periodic')
def run_cron_generate_out_events():
    cron_generate_out_events()
