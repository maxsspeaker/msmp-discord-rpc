import os,sys
from PySide6.QtGui import QAction,QIcon
from PySide6.QtCore import Qt
from modules.types import PluginBase
from .discordrpcWrapper import discordrpcWrapper


class DiscordRpc(PluginBase):
    def init_plugin(self):
        self.my_folder = os.path.dirname(__file__)

        self.base_dir = os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__))

        self.discordrpc = discordrpcWrapper(self.main_window)

        self.DiscordRPCMenu=self.main_window.MainMenuBar.add_submenu(self.main_window.PlguinMenu, "DiscordRpc", hide_if_empty=False)

        #self.DiscordRPCMenu.addAction("Toggle DiscordRPC", self.toggle)


        self.main_window.events.on_update_current_metadata.connect(self.discordrpc.set_activity)
        self.main_window.events.on_sync_position.connect(self.discordrpc.sync_position)
        self.main_window.events.on_play_status_changed.connect(self.discordrpc.set_playback_status)

        self.main_window.events.on_app_closing.connect(self.cleanup)

    def toggle(self):
        pass

    def cleanup(self):
        if(self.discordrpc.rpc):
            self.discordrpc.rpc.disconnect()