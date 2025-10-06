import logging
import time
from functools import wraps

def setup_logger() -> logging.Logger:
    logger = logging.getLogger("cinebot")
    handler = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def log_command(func):
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        start = time.perf_counter()
        try:
            res = await func(self, ctx, *args, **kwargs)
            ok = True
            return res
        except Exception as e:
            ok = False
            if hasattr(self, "bot"):
                self.bot.logger.exception("command_error", exc_info=e)
            else:
                import logging as _l
                _l.exception("command_error", exc_info=e)
            raise
        finally:
            dur = int((time.perf_counter() - start) * 1000)
            logger = getattr(self, "bot", None) and self.bot.logger or None
            if logger:
                logger.info(f"cmd={func.__name__} ms={dur} ok={ok} user={getattr(ctx.author,'id',None)}")
    return wrapper
