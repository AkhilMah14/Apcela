import functools
import typing

class RedisStatus:
    QUEUED = 'queued'
    FINISHED = 'finished'
    FAILED = 'failed'
    STARTED = 'started'
    DEFERRED = 'deferred'
    SCHEDULED = 'scheduled'

    valid_status = [
        'queued',
        'finished',
        'failed',
        'started',
        'deferred',
        'scheduled'
    ]

    failed_status = [
        'failed'
    ]

    done_status = [
        'failed',
        'finished'
    ]

    ok_status = [
        'queued',
        'finished',
        'started',
        'deferred',
        'scheduled'
    ]

    def __contains__(self, item):
        return item in self.valid_status


redis_status = RedisStatus()


class NetpalmStatus:
    SUCCESS = 'success'

    valid_status = [
        'success',
        'error'
    ]

    failed_status = [
        'error'
    ]

    ok_status = [
        'success'
    ]

    def __contains__(self, item):
        return item in self.valid_status


netpalm_status = NetpalmStatus()


def format_sf_custom_field(o_field_name: str, multiple=False) -> typing.Union[str, typing.List[str]]:
    n_field_name = f'{o_field_name.title()}__c'

    rslt = [
        o_field_name,
        o_field_name.title(),
        f'{o_field_name.title()}__c',
        f'{o_field_name}__c'
    ]

    return rslt if multiple else n_field_name


def sort(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        value = func(*args, **kwargs)
        try:
            value = list(sorted(value))
        except TypeError:
            pass
        return value

    return wrapper_decorator


def simplify_ordered_dict(od: typing.Union[typing.OrderedDict, typing.Dict]) -> typing.Union[typing.Dict,
                                                                                             typing.List[typing.Dict]]:
    if isinstance(od, typing.List):
        return [simplify_ordered_dict(item) for item in od]

    new_dict = dict(od)
    for key, val in new_dict.items():
        if isinstance(val, typing.OrderedDict):
            new_dict[key] = dict(val)

    return new_dict
