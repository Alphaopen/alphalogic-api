import time
from callbox.logger import log

def run(*argv_r, **kwargs_r):
    def decorator(func):
        def wrapped(device):
            try:
                with device.mutex:
                    if not device.flag_removing:
                        time_start = time.time()
                        func(device)
                        time_finish = time.time()
                        time_spend = time_finish-time_start
                        log.info('run function {0} of device {2} was executed for {1} seconds'.
                                 format(func.func_name, time_spend, device.id))

                        period = getattr(device, kwargs_r.keys()[0]).val
                        if time_spend < period:
                            device.manager.tasks_pool.add_task(time_finish+period-time_spend,
                                                               getattr(device, func.func_name))
                        else:
                            device.manager.tasks_pool.add_task(time_finish, getattr(device, func.func_name))
            except Exception, err:
                log.error(str(err))
        wrapped.runnable = True
        wrapped.period_name = kwargs_r.keys()[0]
        wrapped.period_default_value = kwargs_r.values()[0]
        return wrapped
    return decorator