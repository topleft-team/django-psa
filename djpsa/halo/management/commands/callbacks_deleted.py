from djpsa.sync.management.commands.base_callbacks_deleted import \
    BaseDeleteCommand
from djpsa.halo.callbacks import HaloCallbacksHandler


class Command(BaseDeleteCommand):
    callback_handler = HaloCallbacksHandler
