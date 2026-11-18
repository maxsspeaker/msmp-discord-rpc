import os,sys
import time
import traceback
import yaml

from PySide6.QtGui import QAction,QIcon
from PySide6.QtCore import Qt,QTimer, Slot

from modules.types import PluginBase
from modules.other import LocalSaveDir

from . import discordrpc


class DiscordRpc(PluginBase):
    def init_plugin(self):
        self.my_folder = os.path.dirname(__file__)

        self.base_dir = os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__))
        self.DiscordRPCMenu=self.main_window.MainMenuBar.add_submenu(self.main_window.PluginMenu, "DiscordRpc", hide_if_empty=False)
        self.DiscordRPCMenu.addAction("Toggle DiscordRPC", self.toggle)

        if(os.path.isfile(os.path.join(LocalSaveDir(),"discordrpc","config.yml"))):
            with open(os.path.join(LocalSaveDir(),"discordrpc","config.yml"), "r", encoding="utf-8") as file:
                self.config = yaml.safe_load(file)
        else:
            self.config = {"discordrpcEnabled":True}

            os.makedirs(os.path.join(LocalSaveDir(),"discordrpc"), exist_ok=True)
            with open(os.path.join(LocalSaveDir(),"discordrpc","config.yml"), "w", encoding="utf-8") as file:
                yaml.dump(self.config , file, default_flow_style=False, allow_unicode=True)


        self.timer = QTimer(self.main_window)
        self.timer.setInterval(5000) 
        self.timer.timeout.connect(self.update_activity)

        self.main_window.events.on_update_current_metadata.connect(self.give_queue_activity)
        self.main_window.events.on_sync_position.connect(self.give_queue_time)
        self.main_window.events.on_play_status_changed.connect(self.set_status)

        self.reconnectTimer = QTimer(self.main_window)
        self.reconnectTimer.setInterval(360000) 
        self.reconnectTimer.timeout.connect(self.reconnect_activity)

        self.discordrpcEnabled=self.config["discordrpcEnabled"]

        try:
            self.rpc = discordrpc.RPC(app_id=811577404279619634)
        except Exception:
            traceback.print_exc()
            self.rpc = None

        self.statusBuffer=None
        self.statusNeedChange=False
        self.playningStatus="Stopped"

        self.main_window.events.on_app_closing.connect(self.cleanup)

    def cleanup(self):
        self.config["discordrpcEnabled"]=self.discordrpcEnabled

        with open(os.path.join(LocalSaveDir(),"discordrpc","config.yml"), "w", encoding="utf-8") as file:
                yaml.dump(self.config , file, default_flow_style=False, allow_unicode=True)

    def reconnect_activity(self):
        try:
            self.rpc = discordrpc.RPC(app_id=811577404279619634)
            self.reconnectTimer.stop()
            self.timer.start()
            self.statusNeedChange=True
        except ConnectionRefusedError:
            pass
        except Exception:
            traceback.print_exc()


    def set_status(self,status):
        if not(self.discordrpcEnabled):
            return

        self.playningStatus=status
        if(status=="Playing"):
            self.timer.start()
        else:
            try:
                self.rpc.clear()
            except SystemExit:
                self.rpc=None
                self.reconnectTimer.start()
            except NoneType:
                self.reconnectTimer.start()
            self.timer.stop()

    def toggle(self):
        self.discordrpcEnabled = (not self.discordrpcEnabled)

        if not(self.discordrpcEnabled):
            try:
                self.rpc.clear()
            except SystemExit:
                self.rpc=None
            except NoneType:
                self.reconnectTimer.start()
            self.timer.stop()
        else:
            self.timer.start()
            if not(self.rpc):
                self.reconnectTimer.start()

    def give_queue_activity(self,item):
        self.statusBuffer=item
        if self.discordrpcEnabled:
            self.statusNeedChange=True

    def give_queue_time(self,position_ms: int):
        if self.discordrpcEnabled:
            self.statusNeedChange=True

    @Slot()
    def update_activity(self):
        if(self.statusNeedChange):
            try:
                if(self.rpc):
                    if(self.playningStatus=="Playing"):
                        is_broadcasting=getattr(self.main_window, "is_broadcasting", False)

                        self.rpc.set_activity(
                            state=self.statusBuffer.uploader or "Unknown artist",
                            details=self.statusBuffer.title,
                            act_type=discordrpc.Activity.Listening,
                            ts_start=int(time.time()) - int(self.main_window.player.position()/1000),
                            ts_end=int(time.time()) + self.statusBuffer.duration - int(self.main_window.player.position()/1000),
                            large_image=self.statusBuffer.artwork_url or "msmpwave",
                            small_image="streaming" if is_broadcasting else None,#self.Status.lower(),
                            small_text="broadcasting" if is_broadcasting else None,
                            large_text=self.statusBuffer.album or self.main_window.playlistManager.playlist_title or None
                            )
                    else:
                        self.rpc.clear()
            except SystemExit:
                self.rpc=None
                self.reconnectTimer.start()
                    
            self.statusNeedChange=False
