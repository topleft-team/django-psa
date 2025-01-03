from djpsa.sync.management.commands.base_callbacks_registered import \
    BaseRegisterCommand
from djpsa.halo.callbacks import HaloCallbacksHandler


class Command(BaseRegisterCommand):
    callback_handler = HaloCallbacksHandler
