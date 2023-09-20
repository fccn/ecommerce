"""NAU custom Devstack settings with the objective to configure paygate using devstack"""

from ecommerce.settings.devstack import *


def merge(a: dict, b: dict, path=[]):
    """
    Deep merge dictionaries

    Ref: https://stackoverflow.com/a/7205107
    """
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] != b[key]:
                raise Exception("Conflict at " + ".".join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a


PAYMENT_PROCESSOR_CONFIG = merge(
    PAYMENT_PROCESSOR_CONFIG,
    {
        "edx": {
            "paygate": {
                # development configurations for the paygate
            }
        }
    },
)

PAYMENT_PROCESSORS.append("paygate.processor.PayGate")

EXTRA_PAYMENT_PROCESSOR_URLS = {"paygate": "paygate.urls"}
