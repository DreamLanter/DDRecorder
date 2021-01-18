import os
import datetime
import logging
import platform
import ctypes
from enum import Enum
import prettytable as pt

def is_windows() -> bool:
    plat_sys = platform.system()
    return plat_sys == "Windows"

if is_windows():
    import winreg


def get_log_level(config: dict) -> int:
    if config['root']['logger']['log_level'] == 'DEBUG':
        return logging.DEBUG
    if config['root']['logger']['log_level'] == 'INFO':
        return logging.INFO
    if config['root']['logger']['log_level'] == 'WARN':
        return logging.WARN
    if config['root']['logger']['log_level'] == 'ERROR':
        return logging.ERROR
    return logging.INFO


def check_and_create_dir(dirs: str) -> None:
    if not os.path.exists(dirs):
        os.mkdir(dirs)


def init_data_dirs(root_dir: str = os.getcwd()) -> None:
    check_and_create_dir(os.path.join(root_dir, 'data'))
    check_and_create_dir(os.path.join(root_dir, 'data', 'records'))
    check_and_create_dir(os.path.join(root_dir, 'data', 'merged'))
    check_and_create_dir(os.path.join(root_dir, 'data', 'merge_confs'))
    check_and_create_dir(os.path.join(root_dir, 'data', 'danmu'))
    check_and_create_dir(os.path.join(root_dir, 'data', 'outputs'))
    check_and_create_dir(os.path.join(root_dir, 'data', 'splits'))


def init_record_dir(room_id: str, global_start: datetime.datetime, root_dir: str = os.getcwd()) -> str:
    dirs = os.path.join(root_dir, 'data', 'records',
                        f"{room_id}_{global_start.strftime('%Y-%m-%d_%H-%M-%S')}")
    check_and_create_dir(dirs)
    return dirs


def init_danmu_log_file(room_id: str, global_start: datetime.datetime, root_dir: str = os.getcwd()) -> str:
    log_filename = os.path.join(
        root_dir, 'data', 'danmu', f"{room_id}_{global_start.strftime('%Y-%m-%d_%H-%M-%S')}_danmu.log")
    return log_filename


def generate_filename(room_id: str) -> str:
    return f"{room_id}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.flv"


def get_global_start_from_records(record_dir: str) -> datetime.datetime:
    base = os.path.basename(record_dir)
    return datetime.datetime.strptime(" ".join(base.split("_")[1:3]), '%Y-%m-%d %H-%M-%S')


def get_mergd_filename(room_id: str, global_start: datetime.datetime, root_dir: str = os.getcwd()) -> str:
    filename = os.path.join(root_dir, 'data', 'merged',
                            f"{room_id}_{global_start.strftime('%Y-%m-%d_%H-%M-%S')}_merged.mp4")
    return filename


def init_outputs_dir(room_id: str, global_start: datetime.datetime, root_dir: str = os.getcwd()) -> str:
    dirs = os.path.join(root_dir, 'data', 'outputs',
                        f"{room_id}_{global_start.strftime('%Y-%m-%d_%H-%M-%S')}")
    check_and_create_dir(dirs)
    return dirs


def init_splits_dir(room_id: str, global_start: datetime.datetime, root_dir: str = os.getcwd()) -> str:
    dirs = os.path.join(root_dir, 'data', 'splits',
                        f"{room_id}_{global_start.strftime('%Y-%m-%d_%H-%M-%S')}")
    check_and_create_dir(dirs)
    return dirs


def get_merge_conf_path(room_id: str, global_start: datetime.datetime, root_dir: str = os.getcwd()) -> str:
    filename = os.path.join(root_dir, 'data', 'merge_confs',
                            f"{room_id}_{global_start.strftime('%Y-%m-%d_%H-%M-%S')}_merge_conf.txt")
    return filename


def del_files_and_dir(dirs: str) -> None:
    for filename in os.listdir(dirs):
        os.remove(os.path.join(dirs, filename))
    os.rmdir(dirs)

def refresh_reg() -> None:
    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x1A

    SMTO_ABORTIFHUNG = 0x0002

    result = ctypes.c_long()
    SendMessageTimeoutW = ctypes.windll.user32.SendMessageTimeoutW
    SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0,
                        u'Environment', SMTO_ABORTIFHUNG, 5000, ctypes.byref(result))


def add_path(path: str) -> None:
    abs_path = os.path.abspath(path)
    path_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                              'Environment', 0, winreg.KEY_ALL_ACCESS)
    path_value = winreg.QueryValueEx(path_key, 'Path')
    print(path_value)
    winreg.SetValueEx(path_key, "Path", 0,
                      winreg.REG_EXPAND_SZ, path_value[0]+abs_path+";")
    refresh_reg()


class state(Enum):
    ERROR = -1
    WAITING_FOR_LIVE_START = 0
    LIVE_STARTED = 1
    PROCESSING_RECORDS = 2
    UPLOADING_TO_BILIBILI = 3
    UPLOADING_TO_BAIDUYUN = 4

    def __str__(self):
        if self.value == -1:
            return "错误！"
        if self.value == 0:
            return "摸鱼中"
        if self.value == 1:
            return "开播了"
        if self.value == 2:
            return "正在处理视频"
        if self.value == 3:
            return "正在上传至Bilibili"
        if self.value == 4:
            return "正在上传至百度网盘"


def print_log(runner_list: list) -> str:
    tb = pt.PrettyTable()
    tb.field_names = ["平台", "房间号", "直播状态", "程序状态", "状态变化时间"]
    for runner in runner_list:
        tb.add_row([runner.bl.site_name, runner.bl.room_id, runner.bl.live_status, str(
            runner.current_state), runner.state_change_time])
    print(f"    DDRecorder  当前时间：{datetime.datetime.now()}\n")
    print(tb)
