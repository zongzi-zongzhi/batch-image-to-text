from __future__ import annotations

import argparse
import ctypes
import json
import re
import threading
from typing import Any
from collections.abc import Callable
from pathlib import Path
from tkinter import BooleanVar, Button, Canvas, Checkbutton, Entry, Label, StringVar, Tk, filedialog, messagebox
from tkinter import font as tkfont
from tkinter import ttk

from .exporters import export_all
from .ocr_engine import PaddleOcrEngine, find_images

ProgressCallback = Callable[[int, int, Path | None], None]

DEFAULT_LAYOUT = {
    "window_width": 980,
    "window_height": 720,
    "card_width": 860,
    "card_height": 540,
    "card_x_offset": -2,
    "card_top_offset": -12,
    "card_border_radius": 12,
    "card_border_width": 1,
    "card_padding_left": 30,
    "field_x_offset": 150,
    "path_field_width": 560,
    "subfolder_field_width": 590,
    "button_width": 104,
    "button_gap": 12,
    "start_button_width": 210,
    "progress_gap_after_help": 145,
    "progress_text_left_offset": -90,
    "progress_text_width": 130,
    "current_file_left_gap": 230,
}

DEFAULT_WIDGET_LAYOUT = {
    "start_button": {
        "x": 307,
        "y": 483,
        "width": 210,
        "height": 42,
    },
    "progress_text": {
        "x": 359,
        "y": 433,
        "width": 130,
        "height": 23,
    },
    "progress_bar": {
        "x": 150,
        "y": 463,
        "width": 590,
        "height": 10,
    },
}

EDITABLE_WIDGETS = {
    "card": "主面板边框",
    "input_value": "图片文件夹输入框",
    "input_button": "图片文件夹选择按钮",
    "output_value": "输出文件夹输入框",
    "output_button": "输出文件夹选择按钮",
    "subfolder_entry": "新文件夹名称输入框",
    "subfolder_help": "可选说明文字",
    "progress_bar": "进度条",
    "progress_text": "进度文字",
    "current_file": "当前文件文字",
    "start_button": "开始提取按钮",
}


def run_batch(
    input_dir: Path,
    output_dir: Path,
    recursive: bool = False,
    progress_callback: ProgressCallback | None = None,
) -> int:
    if not input_dir.exists() or not input_dir.is_dir():
        raise ValueError(f"输入文件夹不存在：{input_dir}")

    images = find_images(input_dir, recursive=recursive)
    if not images:
        raise ValueError(f"没有找到可处理的图片：{input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    total = len(images)
    if progress_callback:
        progress_callback(0, total, None)

    engine = PaddleOcrEngine()
    records = []
    for index, image_path in enumerate(images, start=1):
        if progress_callback:
            progress_callback(index - 1, total, image_path)
        records.append(engine.extract(image_path))
        if progress_callback:
            progress_callback(index, total, image_path)

    export_all(records, output_dir)
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="批量图片转文字")
    parser.add_argument("--input", help="图片文件夹路径")
    parser.add_argument("--output", help="输出文件夹路径")
    parser.add_argument("--recursive", action="store_true", help="包含子文件夹")
    args = parser.parse_args()

    if args.input and args.output:
        count = run_batch(Path(args.input), Path(args.output), recursive=args.recursive)
        print(f"处理完成：{count} 张图片")
        return

    launch_gui()


def launch_gui() -> None:
    enable_windows_dpi_awareness()
    layout = load_layout_config()

    root = Tk()
    root.title("批量图片转文字")
    root.geometry(f"{layout['window_width']}x{layout['window_height']}")
    root.minsize(360, 260)
    root.configure(bg="#ece9e0")

    root.option_add("*Font", ("Microsoft YaHei UI", 11))
    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.configure(family="Microsoft YaHei UI", size=11)
    title_font = tkfont.Font(family="Microsoft YaHei UI", size=21)

    palette = {
        "page": "#ece9e0",
        "panel": "#f7f4ec",
        "field": "#ffffff",
        "field_disabled": "#efece4",
        "border": "#d8d0c2",
        "text": "#141413",
        "muted": "#6b6860",
        "subtle": "#9a9488",
        "choose": "#141413",
        "choose_active": "#262622",
        "primary": "#dd7656",
        "primary_active": "#cf684a",
        "progress_bg": "#ded8cc",
    }

    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    style.configure(
        "Warm.Horizontal.TProgressbar",
        background=palette["primary"],
        troughcolor=palette["progress_bg"],
        bordercolor=palette["progress_bg"],
        lightcolor=palette["primary"],
        darkcolor=palette["primary"],
        thickness=10,
    )

    input_var = StringVar()
    output_var = StringVar()
    input_display_var = StringVar(value="请选择图片所在文件夹")
    output_display_var = StringVar(value="请选择结果保存位置")
    subfolder_name_var = StringVar()
    status_var = StringVar(value="请选择图片文件夹和输出文件夹。")
    progress_text_var = StringVar(value="进度：等待开始")
    current_file_var = StringVar(value="")
    recursive_var = BooleanVar(value=False)
    use_subfolder_var = BooleanVar(value=False)

    def choose_input() -> None:
        path = filedialog.askdirectory(title="选择图片文件夹")
        if path:
            input_var.set(path)
            input_display_var.set(path)

    def choose_output() -> None:
        path = filedialog.askdirectory(title="选择输出文件夹")
        if path:
            output_var.set(path)
            output_display_var.set(path)

    def update_subfolder_state() -> None:
        state = "normal" if use_subfolder_var.get() else "disabled"
        subfolder_entry.config(state=state)

    def set_controls_state(state: str) -> None:
        start_button.config(state=state)

    def on_progress(done: int, total: int, image_path: Path | None) -> None:
        def update() -> None:
            progress_bar["maximum"] = max(total, 1)
            progress_bar["value"] = done
            remaining = max(total - done, 0)
            progress_text_var.set(f"进度：已完成 {done} / {total} 张，还剩 {remaining} 张")
            if image_path:
                current_file_var.set(f"当前：{image_path.name}")
            elif total:
                current_file_var.set("正在准备 OCR 引擎...")

        root.after(0, update)

    def start() -> None:
        if not input_var.get() or not output_var.get():
            messagebox.showwarning("缺少路径", "请先选择图片文件夹和输出文件夹。")
            return

        input_dir = Path(input_var.get())
        output_dir = Path(output_var.get())

        if use_subfolder_var.get():
            subfolder_name = subfolder_name_var.get().strip()
            if not subfolder_name:
                messagebox.showwarning("缺少文件夹名称", "请填写要新建的输出子文件夹名称。")
                return
            if not is_safe_folder_name(subfolder_name):
                messagebox.showwarning("文件夹名称不可用", '文件夹名称不能包含：\\ / : * ? " < > |')
                return
            output_dir = output_dir / subfolder_name

        set_controls_state("disabled")
        progress_bar["value"] = 0
        progress_text_var.set("进度：正在统计图片...")
        current_file_var.set("")
        status_var.set("正在识别，请稍等。批量处理可能需要一些时间。")

        def worker() -> None:
            try:
                count = run_batch(
                    input_dir,
                    output_dir,
                    recursive=recursive_var.get(),
                    progress_callback=on_progress,
                )
            except Exception as exc:  # noqa: BLE001
                root.after(0, lambda: messagebox.showerror("处理失败", str(exc)))
                root.after(0, lambda: status_var.set("处理失败。"))
            else:
                root.after(0, lambda: status_var.set(f"处理完成：{count} 张图片。输出位置：{output_dir}"))
                root.after(0, lambda: current_file_var.set("全部处理完成。"))
                root.after(0, lambda: messagebox.showinfo("处理完成", f"已输出到：\n{output_dir}"))
            finally:
                root.after(0, lambda: set_controls_state("normal"))

        threading.Thread(target=worker, daemon=True).start()

    def draw_rounded_rect(
        canvas: Canvas,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        radius: int,
        border_width: int = 1,
        **kwargs,
    ) -> None:
        fill = kwargs.get("fill", "")
        outline = kwargs.get("outline", "")
        canvas.create_arc(
            x1, y1, x1 + radius * 2, y1 + radius * 2, start=90, extent=90, style="pieslice", fill=fill, outline=fill
        )
        canvas.create_arc(
            x2 - radius * 2,
            y1,
            x2,
            y1 + radius * 2,
            start=0,
            extent=90,
            style="pieslice",
            fill=fill,
            outline=fill,
        )
        canvas.create_arc(
            x2 - radius * 2,
            y2 - radius * 2,
            x2,
            y2,
            start=270,
            extent=90,
            style="pieslice",
            fill=fill,
            outline=fill,
        )
        canvas.create_arc(
            x1,
            y2 - radius * 2,
            x1 + radius * 2,
            y2,
            start=180,
            extent=90,
            style="pieslice",
            fill=fill,
            outline=fill,
        )
        canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline=fill)
        canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill, outline=fill)
        if outline:
            canvas.create_arc(
                x1,
                y1,
                x1 + radius * 2,
                y1 + radius * 2,
                start=90,
                extent=90,
                style="arc",
                outline=outline,
                width=border_width,
            )
            canvas.create_arc(
                x2 - radius * 2,
                y1,
                x2,
                y1 + radius * 2,
                start=0,
                extent=90,
                style="arc",
                outline=outline,
                width=border_width,
            )
            canvas.create_arc(
                x2 - radius * 2,
                y2 - radius * 2,
                x2,
                y2,
                start=270,
                extent=90,
                style="arc",
                outline=outline,
                width=border_width,
            )
            canvas.create_arc(
                x1,
                y2 - radius * 2,
                x1 + radius * 2,
                y2,
                start=180,
                extent=90,
                style="arc",
                outline=outline,
                width=border_width,
            )
            canvas.create_line(x1 + radius, y1, x2 - radius, y1, fill=outline, width=border_width)
            canvas.create_line(x2, y1 + radius, x2, y2 - radius, fill=outline, width=border_width)
            canvas.create_line(x1 + radius, y2, x2 - radius, y2, fill=outline, width=border_width)
            canvas.create_line(x1, y1 + radius, x1, y2 - radius, fill=outline, width=border_width)

    def styled_button(text: str, command, bg: str, active_bg: str, fg: str) -> Button:
        return Button(
            root,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=fg,
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Microsoft YaHei UI", 11, "bold"),
        )

    def draw_spaced_text(canvas: Canvas, x: int, y: int, text: str, spacing: int, font: tkfont.Font, fill: str) -> None:
        current_x = x
        for char in text:
            canvas.create_text(current_x, y, text=char, anchor="nw", fill=fill, font=font)
            current_x += font.measure(char) + spacing

    def make_label(text: str, **kwargs) -> Label:
        label = Label(root, text=text, bg=palette["panel"], fg=kwargs.pop("fg", palette["muted"]), **kwargs)
        return label

    def make_value(variable: StringVar) -> Label:
        label = Label(
            root,
            textvariable=variable,
            anchor="w",
            bg=palette["field"],
            fg=palette["text"] if variable.get() not in {"请选择图片所在文件夹", "请选择结果保存位置"} else palette["subtle"],
            relief="solid",
            bd=1,
            padx=14,
        )

        def update_color(*_: object) -> None:
            label.config(
                fg=palette["subtle"]
                if variable.get() in {"请选择图片所在文件夹", "请选择结果保存位置"}
                else palette["text"]
            )

        variable.trace_add("write", update_color)
        return label

    def make_path_row(label_text: str, variable: StringVar, command) -> tuple[Label, Label, Button]:
        return (
            make_label(label_text),
            make_value(variable),
            styled_button("选择", command, palette["choose"], palette["choose_active"], "#ffffff"),
        )

    canvas = Canvas(root, bg=palette["page"], highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    title_label = Label(
        root,
        text="批量图片转文字",
        bg=palette["panel"],
        fg=palette["text"],
        font=title_font,
        anchor="w",
    )

    subtitle_label = Label(
        root,
        text="选择文件夹，批量识别图片文字并导出结果。",
        bg=palette["panel"],
        fg=palette["subtle"],
        font=("Microsoft YaHei UI", 10),
    )

    input_label, input_value, input_button = make_path_row("图片文件夹", input_display_var, choose_input)
    output_label, output_value, output_button = make_path_row("输出文件夹", output_display_var, choose_output)

    recursive_check = Checkbutton(
        root,
        text="包含子文件夹",
        variable=recursive_var,
        bg=palette["panel"],
        activebackground=palette["panel"],
        fg=palette["muted"],
        selectcolor=palette["field"],
        relief="flat",
        bd=0,
    )
    recursive_help_label = Label(
        root,
        text="勾选后，子文件夹里的图片也会一起处理。",
        bg=palette["panel"],
        fg=palette["subtle"],
        wraplength=760,
        justify="left",
        font=("Microsoft YaHei UI", 10),
    )

    subfolder_check = Checkbutton(
        root,
        text="在输出文件夹中新建子文件夹",
        variable=use_subfolder_var,
        command=update_subfolder_state,
        bg=palette["panel"],
        activebackground=palette["panel"],
        fg=palette["muted"],
        selectcolor=palette["field"],
        relief="flat",
        bd=0,
    )

    subfolder_label = make_label("新文件夹名称")
    subfolder_entry = Entry(
        root,
        textvariable=subfolder_name_var,
        state="disabled",
        relief="solid",
        bd=1,
        bg=palette["field"],
        disabledbackground=palette["field_disabled"],
        disabledforeground=palette["subtle"],
        fg=palette["text"],
    )
    subfolder_help_label = Label(
        root,
        text="可选：勾选后，结果会输出到“输出文件夹 / 新文件夹名称”。",
        bg=palette["panel"],
        fg=palette["subtle"],
        wraplength=760,
        justify="left",
        font=("Microsoft YaHei UI", 10),
    )

    progress_bar = ttk.Progressbar(root, mode="determinate", style="Warm.Horizontal.TProgressbar")
    progress_text_label = Label(
        root, textvariable=progress_text_var, bg=palette["panel"], fg=palette["muted"], justify="left"
    )
    current_file_label = Label(
        root,
        textvariable=current_file_var,
        bg=palette["panel"],
        fg=palette["subtle"],
        wraplength=300,
        justify="left",
    )

    start_button = styled_button(
        "开始提取",
        start,
        palette["primary"],
        palette["primary_active"],
        "#ffffff",
    )

    status_label = Label(
        root,
        textvariable=status_var,
        anchor="w",
        bg=palette["page"],
        fg=palette["text"],
        wraplength=740,
        justify="left",
    )

    edit_mode_var = BooleanVar(value=False)
    selected_widget_name: str | None = None
    selected_widget_var = StringVar(value="")
    widget_overrides: dict[str, dict[str, int]] = layout["widgets"]
    current_widget_boxes: dict[str, dict[str, int]] = {}
    editable_widgets: dict[str, Any] = {}
    drag_state: dict[str, Any] = {}
    card_origin = {"x": 0, "y": 0}
    current_card_box = {"x": 0, "y": 0, "width": layout["card_width"], "height": layout["card_height"]}

    def enter_edit_mode() -> None:
        edit_mode_var.set(True)
        selected_widget_var.set("拖动元素移动；拖右边缘调整宽度。")
        status_var.set("正在调整布局。满意后点击“保存布局”。")
        layout_widgets()

    def exit_edit_mode() -> None:
        edit_mode_var.set(False)
        clear_selection()
        selected_widget_var.set("")
        status_var.set("请选择图片文件夹和输出文件夹。")
        layout_widgets()

    def save_current_layout() -> None:
        layout["widgets"] = widget_overrides
        save_layout_config(layout)
        messagebox.showinfo("布局已保存", "布局已保存。下次启动会继续使用当前位置。")

    edit_button = styled_button("调整布局", enter_edit_mode, palette["choose"], palette["choose_active"], "#ffffff")
    save_layout_button = styled_button("保存布局", save_current_layout, palette["primary"], palette["primary_active"], "#ffffff")
    exit_edit_button = styled_button("退出调整", exit_edit_mode, palette["choose"], palette["choose_active"], "#ffffff")
    selected_widget_label = Label(
        root,
        textvariable=selected_widget_var,
        anchor="e",
        bg=palette["panel"],
        fg=palette["subtle"],
        font=("Microsoft YaHei UI", 9),
    )

    def clear_selection() -> None:
        nonlocal selected_widget_name
        selected_widget_name = None
        for widget in editable_widgets.values():
            try:
                widget.config(highlightthickness=0)
            except Exception:
                pass

    def select_widget(name: str) -> None:
        nonlocal selected_widget_name
        selected_widget_name = name
        selected_widget_var.set(f"已选中：{EDITABLE_WIDGETS[name]}")
        for widget_name, widget in editable_widgets.items():
            try:
                if widget_name == name:
                    widget.config(highlightbackground=palette["primary"], highlightthickness=2)
                else:
                    widget.config(highlightthickness=0)
            except Exception:
                pass

    def place_editable(name: str, widget: Any, x: int, y: int, width: int, height: int) -> None:
        override = widget_overrides.get(name)
        if override:
            x = card_origin["x"] + override["x"]
            y = card_origin["y"] + override["y"]
            width = override["width"]
            height = override["height"]
        widget.place(x=x, y=y, width=width, height=height)
        current_widget_boxes[name] = {
            "x": int(x - card_origin["x"]),
            "y": int(y - card_origin["y"]),
            "width": int(width),
            "height": int(height),
        }

    def on_edit_press(name: str, event: Any) -> str | None:
        if not edit_mode_var.get():
            return None

        select_widget(name)
        box = current_widget_boxes.get(name)
        if not box:
            widget = editable_widgets[name]
            box = {
                "x": int(widget.winfo_x() - card_origin["x"]),
                "y": int(widget.winfo_y() - card_origin["y"]),
                "width": int(widget.winfo_width()),
                "height": int(widget.winfo_height()),
            }
        drag_state.clear()
        resize_width = event.x >= max(box["width"] - 12, 0)
        resize_height = event.y >= max(box["height"] - 12, 0)
        drag_mode = "move"
        if resize_width and resize_height:
            drag_mode = "resize_both"
        elif resize_width:
            drag_mode = "resize_width"
        elif resize_height:
            drag_mode = "resize_height"

        drag_state.update(
            {
                "name": name,
                "start_x": event.x_root,
                "start_y": event.y_root,
                "box": box.copy(),
                "mode": drag_mode,
            }
        )
        return "break"

    def on_edit_drag(event: Any) -> str | None:
        if not edit_mode_var.get() or not drag_state:
            return None

        name = drag_state["name"]
        start_box = drag_state["box"]
        dx = event.x_root - drag_state["start_x"]
        dy = event.y_root - drag_state["start_y"]
        new_box = start_box.copy()
        if drag_state["mode"] in {"resize_width", "resize_both"}:
            new_box["width"] = max(10, int(start_box["width"] + dx))
        if drag_state["mode"] in {"resize_height", "resize_both"}:
            new_box["height"] = max(8, int(start_box["height"] + dy))
        if drag_state["mode"] == "move":
            new_box["x"] = int(start_box["x"] + dx)
            new_box["y"] = int(start_box["y"] + dy)

        if name == "card":
            root_width = max(root.winfo_width(), 1)
            root_height = max(root.winfo_height(), 1)
            layout["card_width"] = new_box["width"]
            layout["card_height"] = new_box["height"]
            layout["card_x_offset"] = int(new_box["x"] - int((root_width - new_box["width"]) / 2))
            layout["card_top_offset"] = int(new_box["y"] - int((root_height - new_box["height"]) / 2))
            layout_widgets()
            return "break"

        widget_overrides[name] = new_box
        widget = editable_widgets[name]
        widget.place(
            x=card_origin["x"] + new_box["x"],
            y=card_origin["y"] + new_box["y"],
            width=new_box["width"],
            height=new_box["height"],
        )
        current_widget_boxes[name] = new_box
        return "break"

    def on_edit_release(event: Any) -> str | None:
        if not edit_mode_var.get():
            return None
        drag_state.clear()
        return "break"

    def bind_editable(name: str, widget: Any) -> None:
        editable_widgets[name] = widget
        widget.bind("<ButtonPress-1>", lambda event, widget_name=name: on_edit_press(widget_name, event))
        widget.bind("<B1-Motion>", on_edit_drag)
        widget.bind("<ButtonRelease-1>", on_edit_release)

    def on_card_press(event: Any) -> str | None:
        if not edit_mode_var.get():
            return None
        box = current_card_box
        inside_x = box["x"] <= event.x <= box["x"] + box["width"]
        inside_y = box["y"] <= event.y <= box["y"] + box["height"]
        if not inside_x or not inside_y:
            return None

        select_widget("card")
        resize_width = event.x >= box["x"] + max(box["width"] - 14, 0)
        resize_height = event.y >= box["y"] + max(box["height"] - 14, 0)
        drag_mode = "move"
        if resize_width and resize_height:
            drag_mode = "resize_both"
        elif resize_width:
            drag_mode = "resize_width"
        elif resize_height:
            drag_mode = "resize_height"

        drag_state.clear()
        drag_state.update(
            {
                "name": "card",
                "start_x": event.x_root,
                "start_y": event.y_root,
                "box": box.copy(),
                "mode": drag_mode,
            }
        )
        return "break"

    for widget_name, widget in {
        "input_value": input_value,
        "input_button": input_button,
        "output_value": output_value,
        "output_button": output_button,
        "subfolder_entry": subfolder_entry,
        "subfolder_help": subfolder_help_label,
        "progress_bar": progress_bar,
        "progress_text": progress_text_label,
        "current_file": current_file_label,
        "start_button": start_button,
    }.items():
        bind_editable(widget_name, widget)

    def layout_widgets(event: object | None = None) -> None:
        width = max(root.winfo_width(), 1)
        height = max(root.winfo_height(), 1)
        canvas.delete("all")
        canvas.create_rectangle(0, 0, width, height, fill=palette["page"], outline="")
        canvas.create_oval(-160, -160, 260, 220, fill="#eadfd5", outline="")
        canvas.create_oval(width - 290, -180, width + 170, 240, fill="#e4e6dc", outline="")
        canvas.create_oval(width * 0.56, height - 170, width + 120, height + 170, fill="#e9e3d4", outline="")

        card_width = layout["card_width"]
        card_height = layout["card_height"]
        card_x = int((width - card_width) / 2) + layout["card_x_offset"]
        card_y = int((height - card_height) / 2) + layout["card_top_offset"]
        card_bottom = card_y + card_height
        card_origin["x"] = card_x
        card_origin["y"] = card_y
        current_card_box.update({"x": card_x, "y": card_y, "width": card_width, "height": card_height})
        draw_rounded_rect(
            canvas,
            card_x,
            card_y,
            card_x + card_width,
            card_bottom,
            layout["card_border_radius"],
            border_width=layout["card_border_width"],
            fill=palette["panel"],
            outline=palette["border"],
        )
        if edit_mode_var.get() and selected_widget_name == "card":
            canvas.create_rectangle(
                card_x - 4,
                card_y - 4,
                card_x + card_width + 4,
                card_bottom + 4,
                outline=palette["primary"],
                width=2,
                dash=(6, 4),
            )

        left_x = card_x + layout["card_padding_left"]
        field_x = card_x + layout["field_x_offset"]
        button_width = layout["button_width"]
        button_gap = layout["button_gap"]
        field_width = layout["path_field_width"]
        button_x = field_x + field_width + button_gap
        row_height = 42
        first_row_y = card_y + 106
        second_row_y = first_row_y + 58

        title_label.place(x=left_x, y=card_y + 34, width=360, height=42)
        subtitle_label.place(x=left_x + 1, y=card_y + 78)

        if edit_mode_var.get():
            save_layout_button.place(x=card_x + card_width - 286, y=card_y + 30, width=88, height=32)
            edit_button.place(x=card_x + card_width - 190, y=card_y + 30, width=88, height=32)
            exit_edit_button.place(x=card_x + card_width - 94, y=card_y + 30, width=88, height=32)
            selected_widget_label.place(x=card_x + card_width - 380, y=card_y + 66, width=374, height=24)
        else:
            edit_button.place(x=card_x + card_width - 190, y=card_y + 30, width=88, height=32)
            save_layout_button.place_forget()
            exit_edit_button.place_forget()
            selected_widget_label.place_forget()

        for label, value_name, value, button_name, button, y in (
            (input_label, "input_value", input_value, "input_button", input_button, first_row_y),
            (output_label, "output_value", output_value, "output_button", output_button, second_row_y),
        ):
            label.place(x=left_x, y=y + 9)
            place_editable(value_name, value, field_x, y, field_width, row_height)
            place_editable(button_name, button, button_x, y, button_width, row_height)

        option_x = field_x
        recursive_y = card_y + 246
        recursive_check.place(x=option_x, y=recursive_y)
        recursive_help_label.place(x=option_x + 28, y=recursive_y + 28)

        subfolder_y = card_y + 318
        subfolder_check.place(x=option_x, y=subfolder_y)
        subfolder_label.place(x=left_x, y=subfolder_y + 43)
        text_field_width = layout["subfolder_field_width"]
        place_editable("subfolder_entry", subfolder_entry, field_x, subfolder_y + 32, text_field_width, 42)
        place_editable("subfolder_help", subfolder_help_label, field_x, subfolder_y + 80, text_field_width, 24)

        progress_y = subfolder_y + layout["progress_gap_after_help"]
        progress_width = text_field_width
        place_editable("progress_bar", progress_bar, field_x, progress_y, progress_width, 10)
        control_y = progress_y + 20
        start_button_width = layout["start_button_width"]
        start_button_x = field_x + int((progress_width - start_button_width) / 2)
        place_editable(
            "progress_text",
            progress_text_label,
            start_button_x + layout["progress_text_left_offset"],
            control_y + 10,
            layout["progress_text_width"],
            24,
        )
        current_file_width = max(220, progress_width - layout["current_file_left_gap"] - 210)
        current_file_label.config(wraplength=current_file_width)
        place_editable(
            "current_file",
            current_file_label,
            start_button_x + layout["current_file_left_gap"],
            control_y + 10,
            current_file_width,
            24,
        )
        place_editable("start_button", start_button, start_button_x, control_y, start_button_width, 42)

        status_label.config(wraplength=card_width - 68)
        status_label.place(x=left_x, y=card_bottom + 14, width=card_width - 68, height=28)
        if edit_mode_var.get() and selected_widget_name:
            select_widget(selected_widget_name)

    root.bind("<Configure>", layout_widgets)
    canvas.bind("<ButtonPress-1>", on_card_press)
    canvas.bind("<B1-Motion>", on_edit_drag)
    canvas.bind("<ButtonRelease-1>", on_edit_release)
    root.after(0, layout_widgets)

    root.mainloop()


def enable_windows_dpi_awareness() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def get_layout_config_path() -> Path:
    return Path(__file__).resolve().parent.parent / "ui_layout.json"


def load_layout_config() -> dict[str, Any]:
    config_path = get_layout_config_path()
    layout = DEFAULT_LAYOUT.copy()
    layout["widgets"] = {name: box.copy() for name, box in DEFAULT_WIDGET_LAYOUT.items()}
    if not config_path.exists():
        return layout

    try:
        raw_config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return layout

    for key, default_value in DEFAULT_LAYOUT.items():
        value = raw_config.get(key, default_value)
        if isinstance(value, int):
            layout[key] = value

    widget_config = raw_config.get("widgets", {})
    if isinstance(widget_config, dict):
        widgets: dict[str, dict[str, int]] = layout["widgets"].copy()
        for name, box in widget_config.items():
            if name not in EDITABLE_WIDGETS or not isinstance(box, dict):
                continue
            clean_box: dict[str, int] = {}
            for key in ("x", "y", "width", "height"):
                value = box.get(key)
                if isinstance(value, int):
                    clean_box[key] = value
            if {"x", "y", "width", "height"} <= clean_box.keys():
                widgets[name] = clean_box
        layout["widgets"] = widgets
    return layout


def save_layout_config(layout: dict[str, Any]) -> None:
    config_path = get_layout_config_path()
    clean_layout = {key: int(layout[key]) for key in DEFAULT_LAYOUT if isinstance(layout.get(key), int)}
    clean_layout["widgets"] = layout.get("widgets", {})
    config_path.write_text(json.dumps(clean_layout, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def is_safe_folder_name(name: str) -> bool:
    return bool(name) and not re.search(r'[\\/:*?"<>|]', name)


if __name__ == "__main__":
    main()
