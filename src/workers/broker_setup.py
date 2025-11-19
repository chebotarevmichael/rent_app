import dramatiq
from dramatiq.brokers.redis import RedisBroker
from periodiq import PeriodiqMiddleware

broker = RedisBroker(url="redis://localhost:6379/0")
broker.add_middleware(PeriodiqMiddleware())

dramatiq.set_broker(broker)
