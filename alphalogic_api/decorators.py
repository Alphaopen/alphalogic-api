# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import inspect
import time
import traceback
from alphalogic_api.logger import log
from alphalogic_api import utils


def command_preparation(wrapped, func, **kwargs_c):
    """
    Return value and command arguments setup
    """
    wrapped.result_type = kwargs_c['result_type']
    (args, varargs, keywords, defaults) = inspect.getargspec(func)
    wrapped.__dict__['arguments'] = []
    wrapped.__dict__['arguments_type'] = {}
    wrapped.__dict__['function_name'] = func.__name__
    wrapped.__dict__['choices'] = {}
    for name_arg in filter(lambda x: x in kwargs_c, args):
        wrapped.choices[name_arg] = kwargs_c[name_arg]
    bias = 1 if 'self' in args else 0  # if first arg is self, see from second
    for index, name in enumerate(args[bias:]):
        wrapped.arguments.append((name, defaults[index]))
        wrapped.arguments_type[name] = utils.get_command_argument_type(defaults[index])


def command(*argv_c, **kwargs_c):
    def decorator(func):
        def wrapped(device, *argv, **kwargs):
            try:
                result = func(device, *argv, **kwargs)
                device.__dict__[wrapped.function_name].set_result(result)
                return result
            except Exception, err:
                t = traceback.format_exc()
                log.error(u'Run function exception: {0}'.format(t))
                device.__dict__[wrapped.function_name].set_exception(t)
        command_preparation(wrapped, func, **kwargs_c)
        return wrapped
    return decorator


def run(*argv_r, **kwargs_r):
    """
    This function periodically executed.
    It created Parameter with period in seconds

    Example:

    # Called every 1 second.
    # You can change period by changing parameter 'period_one' value

    @run(period_one=1)
    def run_one(self):
        self.counter.val += 1

    :param argv_r:
    :param kwargs_r:
    :return:
    """
    def decorator(func):
        def wrapped(device):
            try:
                with device.mutex:
                    if not device.flag_removing:
                        time_start = time.time()

                        try:
                            func(device)
                        except Exception, err:
                            t = traceback.format_exc()
                            log.error(u'Run function exception: {0}'.format(t))

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
                t = traceback.format_exc()
                log.error(u'system error in run decorator: {0}'.format(t))

        wrapped.runnable = True
        wrapped.period_name = kwargs_r.keys()[0]
        wrapped.period_default_value = kwargs_r.values()[0]
        return wrapped
    return decorator