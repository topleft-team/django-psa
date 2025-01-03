from djpsa.sync.management.commands.base_list_callbacks import BaseListCommand
from djpsa.halo.callbacks import HaloCallbacksHandler


class Command(BaseListCommand):
    callback_handler = HaloCallbacksHandler
