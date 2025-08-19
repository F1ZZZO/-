import json
from datetime import datetime, date, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from functools import partial

CONFIG_FILE = Path("task_data.json")

INIT_TASK_MAPPING = {
    "red_small_mine": "红小矿",
    "red_medium_mine": "红中矿",
    "red_large_mine": "红大矿",
    "rainbow_mine": "彩矿",
    "elemental_large_mine": "元素大矿",
    "elemental_xl_mine": "元素特大矿",
}

CYCLE_DAYS = {
    "red_small_mine": 2,
    "red_medium_mine": 4,
    "red_large_mine": 6,
    "rainbow_mine": 3,
    "elemental_large_mine": 2,
    "elemental_xl_mine": 3,
}

TASK_LOCATIONS = {
    "red_small_mine": " (危险洞窟-赤色险地)",
    "red_medium_mine": " (危险洞窟-赤色险地)",
    "red_large_mine": " (危险洞窟-赤色险地)",
    "rainbow_mine": " (彩晶深谷-迷晶归途)",
    "elemental_large_mine": " (海底皇城-海王东庭)",
    "elemental_xl_mine": " (海心圣域-浮光小径, 海心圣域-流萤一处)",
    "elemental_giant_mine": " (海心圣域-望角游龙)",
}


def load_data():
    if not CONFIG_FILE.exists():
        return None
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for key, value in data.items():
                if key not in ["dragon_nest_start_week", "guild_boss_start_week"]:
                    data[key] = date.fromisoformat(value)
            return data
    except (json.JSONDecodeError, ValueError):
        return None


def save_data(data):
    data_to_save = {}
    for key, value in data.items():
        if isinstance(value, date):
            data_to_save[key] = value.isoformat()
        else:
            data_to_save[key] = value

    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, indent=4, ensure_ascii=False)


def check_if_task_is_due(task_key, last_date, today):
    days_passed = (today - last_date).days
    required_days = CYCLE_DAYS.get(task_key, 999)
    return days_passed >= required_days



class InitializationWindow(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)
        self.title("首次使用 - 初始化设置")
        self.geometry("450x480")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.parent = parent
        self.combobox_data = {}
        self.grab_set()

        mine_label = ttk.Label(self, text="请选择各项矿物最近一次的挖掘时间:", font=("", 10, "bold"))
        mine_label.pack(pady=(10, 5))

        for key, name in INIT_TASK_MAPPING.items():
            frame = ttk.Frame(self)
            lbl = ttk.Label(frame, text=f"{name}:", width=20, anchor="w")
            lbl.pack(side="left", padx=10)

            cycle = CYCLE_DAYS[key]
            options = ["今天 (0天前)"]
            if cycle > 1:
                options.append("昨天 (1天前)")
            if cycle > 2:
                options.extend([f"{i}天前" for i in range(2, cycle)])
            options.append(f"{cycle}天前 (或不确定)")

            combo = ttk.Combobox(frame, values=options, state="readonly", width=20)
            combo.set(options[0])
            combo.pack(side="left", padx=5)
            self.combobox_data[key] = {'widget': combo, 'options': options}
            frame.pack(pady=4)

        ttk.Separator(self, orient='horizontal').pack(fill='x', pady=15, padx=20)

        weekly_label = ttk.Label(self, text="请分别设置隔周事件的周期:", font=("", 10, "bold"))
        weekly_label.pack(pady=(0, 5))

        dragon_frame = ttk.Frame(self)
        dragon_lbl = ttk.Label(dragon_frame, text="龙巢周期:", width=20, anchor="w")
        dragon_lbl.pack(side="left", padx=10)
        self.dragon_combo = ttk.Combobox(dragon_frame, values=["本周开启", "下周开启"], state="readonly", width=20)
        self.dragon_combo.set("本周开启")
        self.dragon_combo.pack(side="left", padx=5)
        dragon_frame.pack(pady=4)

        boss_frame = ttk.Frame(self)
        boss_lbl = ttk.Label(boss_frame, text="公会Boss周期:", width=20, anchor="w")
        boss_lbl.pack(side="left", padx=10)
        self.boss_combo = ttk.Combobox(boss_frame, values=["本周开启", "下周开启"], state="readonly", width=20)
        self.boss_combo.set("本周开启")
        self.boss_combo.pack(side="left", padx=5)
        boss_frame.pack(pady=4)

        save_button = ttk.Button(self, text="保存并开始", command=self.save_and_start)
        save_button.pack(pady=20)

    def save_and_start(self):
        saved_data = {}
        today = date.today()

        for key, data in self.combobox_data.items():
            selected_option = data['widget'].get()
            days_ago = data['options'].index(selected_option)
            last_completion_date = today - timedelta(days=days_ago)
            saved_data[key] = last_completion_date

        current_week = today.isocalendar()[1]

        if self.dragon_combo.get() == "本周开启":
            saved_data["dragon_nest_start_week"] = current_week
        else:
            saved_data["dragon_nest_start_week"] = current_week - 1

        if self.boss_combo.get() == "本周开启":
            saved_data["guild_boss_start_week"] = current_week
        else:
            saved_data["guild_boss_start_week"] = current_week - 1

        save_data(saved_data)
        messagebox.showinfo("成功", "初始化设置已保存！")
        self.destroy()
        self.parent.load_and_build_ui()

    def on_close(self):
        if messagebox.askokcancel("退出", "您必须完成初始化才能使用程序。确定要退出吗？"):
            self.parent.destroy()


class TodoApp(tk.Tk):
    """主程序窗口"""

    def __init__(self):
        super().__init__()
        self.title("百炼英雄每日代办-由“烟上星雨夜”免费制作，免费程序")
        self.geometry("480x650")
        self.protocol("WM_DELETE_WINDOW", self.save_and_quit)

        self.tasks_with_vars = []
        self.last_completion_dates = load_data()

        if self.last_completion_dates is None:
            self.withdraw()
            InitializationWindow(self)
        else:
            self.build_task_list()

    def load_and_build_ui(self):
        self.last_completion_dates = load_data()
        self.deiconify()
        self.build_task_list()

    def build_task_list(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.tasks_with_vars = []
        header_label = ttk.Label(self, text=f"{date.today().strftime('%Y年%m月%d日')} 待办清单", font=("", 14, "bold"))
        header_label.pack(pady=10)
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(main_frame)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollable_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))


        def _on_mousewheel(event):
            scroll_speed = -1 * (event.delta // 120)
            self.canvas.yview_scroll(scroll_speed, "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        daily_frame = ttk.LabelFrame(scrollable_frame, text="每日常规", padding=(10, 5))
        daily_frame.pack(fill="x", padx=10, pady=5)
        weekly_frame = ttk.LabelFrame(scrollable_frame, text="每周事件", padding=(10, 5))
        weekly_frame.pack(fill="x", padx=10, pady=5)
        mine_frame = ttk.LabelFrame(scrollable_frame, text="周期矿物", padding=(10, 5))
        mine_frame.pack(fill="x", padx=10, pady=5)
        tasks_today = self.generate_tasks()
        for task in tasks_today:
            var = tk.BooleanVar(value=False)
            if task['type'] == 'daily':
                parent_frame = daily_frame
            elif task['type'] == 'weekly':
                parent_frame = weekly_frame
            else:
                parent_frame = mine_frame

            cb = ttk.Checkbutton(parent_frame, text=task['name'], variable=var, padding=5)
            cb.pack(anchor='w', padx=10, pady=2)

            callback = partial(self.on_task_checked, cb, var)
            var.trace_add("write", callback)

            self.tasks_with_vars.append({'task': task, 'var': var, 'widget': cb})

        save_button = ttk.Button(self, text="完成并退出", command=self.save_and_quit)
        save_button.pack(pady=15, side="bottom")

    def on_task_checked(self, widget, var, *args):
        if var.get():
            widget.after(100, widget.destroy)

    def generate_tasks(self):
        today = date.today()
        tasks = []
        daily_tasks = [
            {'name': '元素小矿 (海心圣域-拥环之辉, 海心圣域-深空流金, 海心圣域-蓝影之歌)', 'type': 'daily',
             'key': None},
            {'name': '每日宝箱', 'type': 'daily', 'key': None},
            {'name': '竞技场', 'type': 'daily', 'key': None},
            {'name': '工会任务', 'type': 'daily', 'key': None},
            {'name': '试炼塔', 'type': 'daily', 'key': None},
            {'name': '元素塔', 'type': 'daily', 'key': None},
            {'name': '黑市购买', 'type': 'daily', 'key': None},
            {'name': '百炼村抽奖', 'type': 'daily', 'key': None},
            {'name': '游戏圈', 'type': 'daily', 'key': None},
            {'name': '幸运草采集', 'type': 'daily', 'key': None},
        ]
        tasks.extend(daily_tasks)

        weekly_tasks = []
        if today.weekday() == 0:
            key = 'elemental_giant_mine'
            location = TASK_LOCATIONS.get(key, "")
            weekly_tasks.append({'name': f'元素巨型矿{location}', 'type': 'weekly', 'key': key})

        weekly_tasks.append({'name': '公会战', 'type': 'weekly', 'key': 'guild_war'})

        current_week = today.isocalendar()[1]

        dragon_start_week = self.last_completion_dates.get("dragon_nest_start_week")
        if dragon_start_week is not None:
            if (current_week - dragon_start_week) % 2 == 0:
                weekly_tasks.append({'name': '龙巢 (本周二开启)', 'type': 'weekly', 'key': 'dragon_nest'})

        boss_start_week = self.last_completion_dates.get("guild_boss_start_week")
        if boss_start_week is not None:
            if (current_week - boss_start_week) % 2 == 0:
                weekly_tasks.append({'name': '公会boss (周四开启)', 'type': 'weekly', 'key': 'guild_boss'})

        tasks.extend(weekly_tasks)

        if self.last_completion_dates:
            for key, name in INIT_TASK_MAPPING.items():
                last_date = self.last_completion_dates.get(key)
                if last_date and check_if_task_is_due(key, last_date, today):
                    location = TASK_LOCATIONS.get(key, "")
                    tasks.append({'name': f"{name}{location}", 'type': 'periodic', 'key': key})
        return tasks

    def save_and_quit(self):
        self.unbind_all("<MouseWheel>")

        today = date.today()
        if self.last_completion_dates:
            for item in self.tasks_with_vars:
                task = item['task']
                var = item['var']
                if task['type'] == 'periodic' and var.get():
                    self.last_completion_dates[task['key']] = today

            save_data(self.last_completion_dates)
        self.destroy()


if __name__ == "__main__":
    app = TodoApp()
    app.mainloop()
