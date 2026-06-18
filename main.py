"""
Hotel Calculator App (Android via Kivy)
----------------------------------------
- Custom buttons with fixed values (editable from within the app).
- Each item button adds its value to a running bill.
- "WR" half buttons / fractional handling supported.
- "÷2" mode: divide the next pressed item's value (e.g. 1 plate shared by 2).
- Save every day's calculations under that day's date.
- Edit any button value later (Settings screen) — values persist to disk.

Run on desktop for testing:
    pip install kivy
    python main.py

Build APK with Buildozer (on Linux/WSL):
    pip install buildozer cython
    buildozer -v android debug
"""

import os
import json
import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.utils import platform


# ----------------------------------------------------------------------------
# Storage helpers
# ----------------------------------------------------------------------------
def get_storage_dir():
    """Return a writable directory for saving data (works on Android + desktop)."""
    if platform == "android":
        try:
            from android.storage import app_storage_path  # type: ignore
            base = app_storage_path()
        except Exception:
            base = os.path.dirname(os.path.abspath(__file__))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base, "hotel_calc_data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


STORAGE_DIR = get_storage_dir()
BUTTONS_FILE = os.path.join(STORAGE_DIR, "buttons.json")
HISTORY_FILE = os.path.join(STORAGE_DIR, "history.json")


# Default button definitions: (label, value)
DEFAULT_BUTTONS = [
    {"label": "1F", "value": 1950},
    {"label": "1H", "value": 1050},
    {"label": "1Q", "value": 600},
    {"label": "1FWR", "value": 1650},
    {"label": "1HWR", "value": 850},
    {"label": "1QWR", "value": 450},
    {"label": "1Raita", "value": 70},
    {"label": "1G", "value": 10},
    {"label": "1S", "value": 90},
    {"label": "1L", "value": 180},
    {"label": "1.5L", "value": 230},
    {"label": "2L", "value": 260},
]


def load_buttons():
    if os.path.exists(BUTTONS_FILE):
        try:
            with open(BUTTONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                return data
        except Exception:
            pass
    # First run: write defaults
    save_buttons(DEFAULT_BUTTONS)
    return [dict(b) for b in DEFAULT_BUTTONS]


def save_buttons(buttons):
    with open(BUTTONS_FILE, "w", encoding="utf-8") as f:
        json.dump(buttons, f, indent=2)


def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def fmt(n):
    """Format a number nicely (no trailing .0)."""
    if isinstance(n, float) and n.is_integer():
        n = int(n)
    return f"{n:,}"


# ----------------------------------------------------------------------------
# Calculator Screen
# ----------------------------------------------------------------------------
class CalculatorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.buttons = load_buttons()
        self.total = 0.0
        self.entries = []         # list of (label, value) added this session
        self.half_mode = False    # divide next item value by 2

        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))

        # ---- Top bar ----
        top = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        title = Label(text="[b]Hotel Calculator[/b]", markup=True, font_size="20sp")
        settings_btn = Button(text="Settings", size_hint_x=None, width=dp(110),
                              background_color=(0.30, 0.45, 0.85, 1))
        settings_btn.bind(on_release=self.go_settings)
        history_btn = Button(text="History", size_hint_x=None, width=dp(110),
                             background_color=(0.30, 0.45, 0.85, 1))
        history_btn.bind(on_release=self.go_history)
        top.add_widget(title)
        top.add_widget(history_btn)
        top.add_widget(settings_btn)
        root.add_widget(top)

        # ---- Total display ----
        self.total_label = Label(
            text="Total: 0", markup=True, font_size="30sp",
            size_hint_y=None, height=dp(60),
            color=(0.1, 0.6, 0.2, 1))
        root.add_widget(self.total_label)

        # ---- ÷2 toggle + Clear ----
        controls = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        self.half_btn = Button(text="÷2 mode: OFF",
                               background_color=(0.6, 0.6, 0.6, 1))
        self.half_btn.bind(on_release=self.toggle_half)
        clear_btn = Button(text="Clear", background_color=(0.85, 0.35, 0.35, 1))
        clear_btn.bind(on_release=self.clear_all)
        undo_btn = Button(text="Undo", background_color=(0.85, 0.6, 0.2, 1))
        undo_btn.bind(on_release=self.undo_last)
        controls.add_widget(self.half_btn)
        controls.add_widget(undo_btn)
        controls.add_widget(clear_btn)
        root.add_widget(controls)

        # ---- Item buttons grid (scrollable) ----
        scroll = ScrollView()
        self.grid = GridLayout(cols=3, spacing=dp(6), padding=dp(2),
                               size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        scroll.add_widget(self.grid)
        root.add_widget(scroll)

        # ---- Manual amount + Save row ----
        bottom = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        self.manual_input = TextInput(hint_text="Add custom amount",
                                      multiline=False, input_filter="float")
        add_manual = Button(text="Add", size_hint_x=None, width=dp(80),
                            background_color=(0.30, 0.45, 0.85, 1))
        add_manual.bind(on_release=self.add_manual)
        save_btn = Button(text="Save Today", size_hint_x=None, width=dp(130),
                          background_color=(0.1, 0.6, 0.2, 1))
        save_btn.bind(on_release=self.save_today)
        bottom.add_widget(self.manual_input)
        bottom.add_widget(add_manual)
        bottom.add_widget(save_btn)
        root.add_widget(bottom)

        self.add_widget(root)
        self.build_grid()

    # -- UI building --
    def build_grid(self):
        self.grid.clear_widgets()
        for b in self.buttons:
            btn = Button(
                text=f"{b['label']}\n{fmt(b['value'])}",
                size_hint_y=None, height=dp(72),
                halign="center", valign="middle",
                background_color=(0.20, 0.30, 0.40, 1))
            btn.bind(on_release=lambda inst, item=b: self.add_item(item))
            self.grid.add_widget(btn)

    def refresh_buttons(self):
        self.buttons = load_buttons()
        self.build_grid()

    # -- Actions --
    def toggle_half(self, *_):
        self.half_mode = not self.half_mode
        if self.half_mode:
            self.half_btn.text = "÷2 mode: ON"
            self.half_btn.background_color = (0.1, 0.6, 0.2, 1)
        else:
            self.half_btn.text = "÷2 mode: OFF"
            self.half_btn.background_color = (0.6, 0.6, 0.6, 1)

    def add_item(self, item):
        value = item["value"]
        label = item["label"]
        if self.half_mode:
            value = value / 2
            label = f"{label} (½)"
            # auto turn off after one use
            self.half_mode = False
            self.half_btn.text = "÷2 mode: OFF"
            self.half_btn.background_color = (0.6, 0.6, 0.6, 1)
        self.total += value
        self.entries.append((label, value))
        self.update_total()

    def add_manual(self, *_):
        txt = self.manual_input.text.strip()
        if not txt:
            return
        try:
            value = float(txt)
        except ValueError:
            return
        if self.half_mode:
            value = value / 2
            self.toggle_half()
        self.total += value
        self.entries.append(("Custom", value))
        self.manual_input.text = ""
        self.update_total()

    def undo_last(self, *_):
        if self.entries:
            _, value = self.entries.pop()
            self.total -= value
            self.update_total()

    def clear_all(self, *_):
        self.total = 0.0
        self.entries = []
        self.update_total()

    def update_total(self):
        self.total_label.text = f"Total: [b]{fmt(self.total)}[/b]"

    def save_today(self, *_):
        if not self.entries:
            self.popup("Nothing to save", "Add some items first.")
            return
        history = load_history()
        today = datetime.date.today().isoformat()  # YYYY-MM-DD
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        record = {
            "time": time_str,
            "items": [{"label": l, "value": v} for l, v in self.entries],
            "total": self.total,
        }
        history.setdefault(today, []).append(record)
        save_history(history)
        self.popup("Saved!",
                   f"Saved {len(self.entries)} item(s) for {today}\n"
                   f"Total: {fmt(self.total)}")
        self.clear_all()

    def go_settings(self, *_):
        self.manager.get_screen("settings").refresh()
        self.manager.current = "settings"

    def go_history(self, *_):
        self.manager.get_screen("history").refresh()
        self.manager.current = "history"

    def popup(self, title, message):
        content = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        content.add_widget(Label(text=message))
        close = Button(text="OK", size_hint_y=None, height=dp(44))
        content.add_widget(close)
        pop = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        close.bind(on_release=pop.dismiss)
        pop.open()


# ----------------------------------------------------------------------------
# Settings Screen (edit button values + add/remove)
# ----------------------------------------------------------------------------
class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rows = []  # list of (label_input, value_input, button_dict)

        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))

        top = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        back = Button(text="< Back", size_hint_x=None, width=dp(100),
                      background_color=(0.30, 0.45, 0.85, 1))
        back.bind(on_release=self.go_back)
        top.add_widget(back)
        top.add_widget(Label(text="[b]Edit Buttons[/b]", markup=True,
                             font_size="20sp"))
        root.add_widget(top)

        scroll = ScrollView()
        self.list_box = GridLayout(cols=1, spacing=dp(6), size_hint_y=None,
                                   padding=dp(2))
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll.add_widget(self.list_box)
        root.add_widget(scroll)

        bottom = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        add_btn = Button(text="+ Add Button",
                         background_color=(0.30, 0.45, 0.85, 1))
        add_btn.bind(on_release=self.add_new_row)
        save_btn = Button(text="Save Changes",
                          background_color=(0.1, 0.6, 0.2, 1))
        save_btn.bind(on_release=self.save_changes)
        bottom.add_widget(add_btn)
        bottom.add_widget(save_btn)
        root.add_widget(bottom)

        self.add_widget(root)

    def refresh(self):
        self.list_box.clear_widgets()
        self.rows = []
        for b in load_buttons():
            self.add_row(b["label"], b["value"])

    def add_row(self, label="", value=0):
        row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        label_in = TextInput(text=str(label), multiline=False, hint_text="Name")
        value_in = TextInput(text=str(value), multiline=False,
                             input_filter="float", hint_text="Value")
        remove = Button(text="X", size_hint_x=None, width=dp(48),
                        background_color=(0.85, 0.35, 0.35, 1))
        entry = {"row": row}
        remove.bind(on_release=lambda inst, r=row, e=entry: self.remove_row(r, e))
        row.add_widget(label_in)
        row.add_widget(value_in)
        row.add_widget(remove)
        self.list_box.add_widget(row)
        entry.update({"label_in": label_in, "value_in": value_in})
        self.rows.append(entry)

    def add_new_row(self, *_):
        self.add_row("New", 0)

    def remove_row(self, row, entry):
        self.list_box.remove_widget(row)
        if entry in self.rows:
            self.rows.remove(entry)

    def save_changes(self, *_):
        new_buttons = []
        for e in self.rows:
            label = e["label_in"].text.strip()
            val_txt = e["value_in"].text.strip()
            if not label:
                continue
            try:
                value = float(val_txt) if val_txt else 0
            except ValueError:
                value = 0
            if value == int(value):
                value = int(value)
            new_buttons.append({"label": label, "value": value})
        save_buttons(new_buttons)
        self.manager.get_screen("calc").refresh_buttons()
        self.go_back()

    def go_back(self, *_):
        self.manager.current = "calc"


# ----------------------------------------------------------------------------
# History Screen (view saved calculations by date)
# ----------------------------------------------------------------------------
class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))

        top = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        back = Button(text="< Back", size_hint_x=None, width=dp(100),
                      background_color=(0.30, 0.45, 0.85, 1))
        back.bind(on_release=self.go_back)
        top.add_widget(back)
        top.add_widget(Label(text="[b]History[/b]", markup=True, font_size="20sp"))
        root.add_widget(top)

        scroll = ScrollView()
        self.box = GridLayout(cols=1, spacing=dp(8), size_hint_y=None,
                              padding=dp(2))
        self.box.bind(minimum_height=self.box.setter("height"))
        scroll.add_widget(self.box)
        root.add_widget(scroll)

        self.add_widget(root)

    def refresh(self):
        self.box.clear_widgets()
        history = load_history()
        if not history:
            self.box.add_widget(Label(text="No saved calculations yet.",
                                      size_hint_y=None, height=dp(40)))
            return
        # Most recent dates first
        for date in sorted(history.keys(), reverse=True):
            records = history[date]
            day_total = sum(r["total"] for r in records)
            header = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
            header.add_widget(Label(
                text=f"[b]{date}[/b]  (Day total: {fmt(day_total)})",
                markup=True, font_size="17sp"))
            del_btn = Button(text="Delete", size_hint_x=None, width=dp(90),
                             background_color=(0.85, 0.35, 0.35, 1))
            del_btn.bind(on_release=lambda inst, d=date: self.delete_date(d))
            header.add_widget(del_btn)
            self.box.add_widget(header)

            for r in records:
                items_txt = ", ".join(
                    f"{it['label']}={fmt(it['value'])}" for it in r["items"])
                txt = f"  [{r['time']}]  {items_txt}\n  Total: {fmt(r['total'])}"
                lbl = Label(text=txt, size_hint_y=None, halign="left",
                            valign="top", font_size="14sp")
                lbl.bind(width=lambda inst, w: setattr(inst, "text_size", (w, None)))
                lbl.bind(texture_size=lambda inst, ts: setattr(inst, "height", ts[1] + dp(8)))
                self.box.add_widget(lbl)

    def delete_date(self, date):
        history = load_history()
        if date in history:
            del history[date]
            save_history(history)
        self.refresh()

    def go_back(self, *_):
        self.manager.current = "calc"


# ----------------------------------------------------------------------------
# App
# ----------------------------------------------------------------------------
class HotelCalcApp(App):
    title = "Hotel Calculator"

    def build(self):
        if platform != "android":
            Window.size = (400, 720)
        sm = ScreenManager()
        sm.add_widget(CalculatorScreen(name="calc"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(HistoryScreen(name="history"))
        return sm


if __name__ == "__main__":
    HotelCalcApp().run()
