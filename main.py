import flet as ft
import os
import platform
import subprocess
from datetime import datetime, time, timedelta

from utils import MAX_UI_FILES, natural_sort_key, format_size
from ui_components import CollapsibleDirectory
from operations import (
    scan_directory, copy_single_file, cut_single_file, delete_single_file,
    batch_copy, batch_cut, batch_delete, generate_export_report
)

# --- ПРЕМИУМ ПАЛИТРА (Minimalist Dark) ---
BG_MAIN = "#0B0C10"         
BG_SIDEBAR = "#12141A"      
BG_CONTAINER = "#181A21"    
BG_HOVER = "#232630"        
BORDER_COLOR = "#252833"    
TEXT_PRIMARY = "#F8FAFC"    
TEXT_SECONDARY = "#94A3B8"  
ACCENT_BLUE = "#3B82F6"     
BTN_COPY = "#10B981"        
BTN_CUT = "#F59E0B"         
BTN_EXPORT = "#64748B"      
BTN_DELETE = "#EF4444"      

def main(page: ft.Page):
    page.title = "Smart Manager v18.0 (Ultimate UX)"
    page.theme_mode = ft.ThemeMode.DARK  
    page.bgcolor = BG_MAIN
    
    page.window.width = 1250 
    page.window.height = 800
    page.padding = 0 
    page.update()

    # --- СЪСТОЯНИЯ ---
    matched_files = [] 
    selected_files = set() 
    target_folder = ["."] 
    has_system_files = [False] 
    global_root_node = [None]
    
    sort_asc = [True] 
    auto_expand_all = [False]
    ui_count = [0]
    limit_reached = [False]
    active_icon_rows = [] 
    single_action = {"type": None, "path": None, "row": None}
    expanded_dirs = set()

    # ==============================================================
    # 1. ГРАФИЧНИ ЕЛЕМЕНТИ
    # ==============================================================
    lbl_folder = ft.Text("Текуща директория (.)", color=TEXT_SECONDARY, italic=True, size=12)
    btn_select_folder = ft.ElevatedButton(
        "📂 Избери папка", color=TEXT_PRIMARY, bgcolor=BORDER_COLOR, width=260, height=45,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    )
    
    tf_start = ft.TextField(label="От дата", value="01/01/2024", width=125, border_color=BORDER_COLOR, focused_border_color=ACCENT_BLUE, text_size=13, content_padding=10)
    tf_end = ft.TextField(label="До дата", value=datetime.now().strftime("%d/%m/%Y"), width=125, border_color=BORDER_COLOR, focused_border_color=ACCENT_BLUE, text_size=13, content_padding=10)
    tf_ext = ft.TextField(label="Разширения (txt, pdf)", hint_text="Всички", border_color=BORDER_COLOR, focused_border_color=ACCENT_BLUE, text_size=13, content_padding=10)
    
    btn_scan = ft.ElevatedButton(
        "🔍 Сканирай", width=260, height=50, bgcolor=ACCENT_BLUE, color=ft.colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)) 
    )
    progress_ring = ft.ProgressRing(width=24, height=24, stroke_width=3, visible=False, color=ACCENT_BLUE)

    dd_sort = ft.Dropdown(
        value="Име",
        options=[ft.dropdown.Option("Име"), ft.dropdown.Option("Размер"), ft.dropdown.Option("Дата"), ft.dropdown.Option("Тип")],
        width=120, height=40, text_size=13, border_color=BORDER_COLOR, focused_border_color=ACCENT_BLUE, content_padding=10
    )
    btn_sort_dir = ft.IconButton(icon=ft.icons.ARROW_UPWARD, tooltip="Посока", icon_color=TEXT_SECONDARY, icon_size=18)

    # --- НОВО: Приветстващ екран (Empty State) ---
    empty_state = ft.Container(
        content=ft.Column([
            ft.Icon(ft.icons.FOLDER_SPECIAL_OUTLINED, size=70, color=BORDER_COLOR),
            ft.Text("Няма сканирани файлове", size=18, color=TEXT_SECONDARY, weight="bold"),
            ft.Text("Изберете директория от левия панел и натиснете 'Сканирай'", size=13, color=TEXT_SECONDARY)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.alignment.center,
        expand=True
    )

    results_list = ft.ListView(expand=True, spacing=5, auto_scroll=False)
    results_list.controls = [empty_state] # Зареждаме празния екран при старт
    
    results_container = ft.Container(content=results_list, expand=True, border=ft.border.all(1, BORDER_COLOR), bgcolor=BG_CONTAINER, padding=15, border_radius=12)
    lbl_summary = ft.Text("Готовност за сканиране...", color=TEXT_SECONDARY, size=13)

    btn_style = ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    btn_copy = ft.ElevatedButton("📁 Копирай", disabled=True, color=ft.colors.WHITE, bgcolor=BTN_COPY, style=btn_style)
    btn_cut_bulk = ft.ElevatedButton("✂️ Изрежи", disabled=True, color=ft.colors.WHITE, bgcolor=BTN_CUT, style=btn_style)
    btn_export = ft.ElevatedButton("📄 Експорт", disabled=True, color=ft.colors.WHITE, bgcolor=BTN_EXPORT, style=btn_style)
    btn_delete = ft.ElevatedButton("🗑️ Изтрий", disabled=True, color=ft.colors.WHITE, bgcolor=BTN_DELETE, style=btn_style)

    scan_picker = ft.FilePicker()
    copy_picker = ft.FilePicker()
    cut_bulk_picker = ft.FilePicker()
    export_picker = ft.FilePicker()
    single_action_picker = ft.FilePicker()
    
    dlg_single_delete = ft.AlertDialog(modal=True, bgcolor=BG_CONTAINER, title=ft.Text(""))
    dlg_sys_cut = ft.AlertDialog(modal=True, bgcolor=BG_CONTAINER, title=ft.Text(""))
    page.overlay.extend([scan_picker, copy_picker, cut_bulk_picker, export_picker, single_action_picker, dlg_single_delete, dlg_sys_cut])

    # ==============================================================
    # 2. ПОМОЩНИ ФУНКЦИИ И ЛОГИКА
    # ==============================================================
    # --- НОВО: Функция за отваряне на файл в ОС ---
    def open_system_file(filepath):
        try:
            if platform.system() == 'Windows':
                os.startfile(filepath)
            elif platform.system() == 'Darwin': # macOS
                subprocess.call(('open', filepath))
            else: # Linux
                subprocess.call(('xdg-open', filepath))
        except Exception as e:
            show_snack(f"Грешка при отваряне: Не може да се стартира файла.", BTN_DELETE)

    def update_dynamic_buttons():
        sel_count = len(selected_files)
        is_multi_select = sel_count > 0
        
        if is_multi_select:
            btn_copy.text = f"📁 Копирай ({sel_count})"
            btn_cut_bulk.text = f"✂️ Изрежи ({sel_count})"
            btn_export.text = f"📄 Експорт ({sel_count})"
            btn_delete.text = f"🗑️ Изтрий ({sel_count})"
        else:
            btn_copy.text = "📁 Копирай Всички"
            btn_cut_bulk.text = "✂️ Изрежи Всички"
            btn_export.text = "📄 Експорт Всички"
            btn_delete.text = "🗑️ Изтрий Всички"
            
        for icon_row in active_icon_rows: 
            icon_row.visible = False
            
        is_empty = len(matched_files) == 0
        btn_copy.disabled = is_empty
        btn_cut_bulk.disabled = is_empty
        btn_export.disabled = is_empty
        btn_delete.disabled = is_empty
        page.update()

    def update_summary_text():
        total_size = sum(f_size for _, f_size, _, _ in matched_files)
        lbl_summary.value = f"✅ Намерени: {len(matched_files)} файла | Размер: {format_size(total_size)}"
        if has_system_files[0]:
            lbl_summary.value += " | ⚠️ Системни файлове!"
            lbl_summary.color = BTN_CUT 
        else:
            lbl_summary.color = BTN_COPY 
            
        if limit_reached[0]: lbl_summary.value += f" | ⚡ Лимит {MAX_UI_FILES}."
        update_dynamic_buttons()

    def remove_file_from_state(path, row_control=None):
        for i, item in enumerate(matched_files):
            if item[0] == path:
                matched_files.pop(i)
                break
        selected_files.discard(path) 
                
        def remove_from_tree(node, target_path):
            for i, f in enumerate(node.files):
                if f[1] == target_path: 
                    node.files.pop(i)
                    return True
            for child in node.children.values():
                if remove_from_tree(child, target_path): return True
            return False
            
        if global_root_node[0]: remove_from_tree(global_root_node[0], path)
        if row_control: row_control.visible = False
        update_summary_text()

    def show_snack(text, color):
        page.snack_bar = ft.SnackBar(ft.Text(text, color=ft.colors.WHITE), bgcolor=color, behavior=ft.SnackBarBehavior.FLOATING)
        page.snack_bar.open = True
        page.update()

    def set_quick_date(days_back, month_start=False, year_start=False):
        now = datetime.now()
        tf_end.value = now.strftime("%d/%m/%Y")
        if month_start: start = now.replace(day=1)
        elif year_start: start = now.replace(month=1, day=1)
        else: start = now - timedelta(days=days_back)
        tf_start.value = start.strftime("%d/%m/%Y")
        page.update()

    # --- СВЪРЗВАНЕ НА ПИКЪРИ ---
    def on_scan_folder_selected(e: ft.FilePickerResultEvent):
        if e.path:
            target_folder[0] = e.path
            lbl_folder.value = f"{e.path}"
            lbl_folder.color = TEXT_PRIMARY
            page.update()
    scan_picker.on_result = on_scan_folder_selected

    def on_copy_folder_selected(e: ft.FilePickerResultEvent):
        if e.path:
            files_to_process = [f[0] for f in matched_files if f[0] in selected_files] if selected_files else [f[0] for f in matched_files]
            count, err_count = batch_copy(files_to_process, e.path, target_folder[0])
            msg = f"Успешно копирани {count} файла."
            if err_count > 0: msg += f" (Грешки: {err_count})"
            show_snack(msg, BTN_COPY if err_count == 0 else BTN_CUT)
    copy_picker.on_result = on_copy_folder_selected

    def on_cut_folder_selected(e: ft.FilePickerResultEvent):
        if e.path:
            files_to_process = [f[0] for f in matched_files if f[0] in selected_files] if selected_files else [f[0] for f in matched_files]
            count, err_count, success_files = batch_cut(files_to_process, e.path, target_folder[0])
            for f_path in success_files: remove_file_from_state(f_path, None) 
            msg = f"Успешно изрязани {count} файла."
            if err_count > 0: msg += f" Възникнаха {err_count} грешки!"
            show_snack(msg, BTN_COPY if err_count == 0 else BTN_CUT)
            redraw_tree() 
            page.update()
    cut_bulk_picker.on_result = on_cut_folder_selected

    def on_export_report_selected(e: ft.FilePickerResultEvent):
        if e.path:
            try:
                generate_export_report(e.path, matched_files, selected_files, target_folder[0])
                show_snack("Списъкът е запазен успешно.", BTN_COPY)
            except Exception as ex: show_snack(f"Грешка: {ex}", BTN_DELETE)
    export_picker.on_result = on_export_report_selected

    def on_single_action_selected(e: ft.FilePickerResultEvent):
        if e.path and single_action["path"]:
            try:
                if single_action["type"] == "copy":
                    if copy_single_file(single_action["path"], e.path):
                        show_snack(f"Копиран в: {e.path}", BTN_COPY)
                    else: show_snack("Източникът и дестинацията съвпадат!", BTN_CUT)
                elif single_action["type"] == "cut":
                    if cut_single_file(single_action["path"], e.path):
                        show_snack(f"Изрязан и преместен в: {e.path}", BTN_COPY)
                        remove_file_from_state(single_action["path"], single_action["row"])
                    else: show_snack("Източникът и дестинацията съвпадат!", BTN_CUT)
            except Exception as ex: show_snack(f"Грешка: {ex}", BTN_DELETE)
    single_action_picker.on_result = on_single_action_selected

    def prompt_single_cut(path, row_control, is_sys):
        if is_sys:
            def close_dlg(e):
                dlg_sys_cut.open = False
                page.update()
            def exec_cut(e):
                dlg_sys_cut.open = False
                single_action.update({"type": "cut", "path": path, "row": row_control})
                single_action_picker.get_directory_path()
                page.update()
            
            dlg_sys_cut.title = ft.Text("🚨 Системен файл!", color="#F87171", weight=ft.FontWeight.BOLD)
            dlg_sys_cut.content = ft.Text(f"Опитвате се да преместите системен файл:\n{os.path.basename(path)}\n\nСигурни ли сте?", color=TEXT_PRIMARY)
            dlg_sys_cut.actions = [
                ft.TextButton("Отказ", on_click=close_dlg, style=ft.ButtonStyle(color=TEXT_SECONDARY)),
                ft.TextButton("Да, премести", on_click=exec_cut, style=ft.ButtonStyle(color=BTN_CUT, bgcolor="#451a03"))
            ]
            dlg_sys_cut.open = True
            page.update()
        else:
            single_action.update({"type": "cut", "path": path, "row": row_control})
            single_action_picker.get_directory_path()

    def prompt_single_delete(path, row_control, is_sys):
        def close_single_dlg(e):
            dlg_single_delete.open = False
            page.update()
        def execute_single_delete(e):
            dlg_single_delete.open = False
            try:
                if delete_single_file(path):
                    show_snack("Файлът беше изтрит.", BTN_DELETE)
                    remove_file_from_state(path, row_control)
            except Exception as ex: show_snack(f"Грешка: {ex}", BTN_DELETE)

        dlg_single_delete.title = ft.Text("🚨 Системен файл!" if is_sys else "Потвърждение", color="#F87171" if is_sys else TEXT_PRIMARY, weight=ft.FontWeight.BOLD)
        content_text = f"Изтриване на:\n{os.path.basename(path)}?"
        if is_sys: content_text += "\n\nТова е системен файл. Изтриването му е опасно!"
        dlg_single_delete.content = ft.Text(content_text, color=TEXT_PRIMARY)
        dlg_single_delete.actions = [
            ft.TextButton("Отказ", on_click=close_single_dlg, style=ft.ButtonStyle(color=TEXT_SECONDARY)),
            ft.TextButton("Да, изтрий", on_click=execute_single_delete, style=ft.ButtonStyle(color=BTN_DELETE, bgcolor="#450a0a"))
        ]
        dlg_single_delete.open = True
        page.update()

    def confirm_bulk_delete_dialog():
        def close_dlg(e):
            dlg.open = False
            page.update()
        def do_delete(e):
            dlg.open = False
            files_to_delete = [f[0] for f in matched_files if f[0] in selected_files] if selected_files else [f[0] for f in matched_files]
            count, err_count, success_files = batch_delete(files_to_delete)
            for f_path in success_files: remove_file_from_state(f_path, None)
            
            msg = f"Успешно изтрити {count} файла."
            if err_count > 0: msg += f" (Грешки: {err_count})"
            show_snack(msg, BTN_DELETE if err_count == 0 else BTN_CUT)
            redraw_tree() 
            page.update()
        
        target_count = len(selected_files) if selected_files else len(matched_files)
        sys_in_target = any(is_sys for f_path, _, _, is_sys in matched_files if (not selected_files or f_path in selected_files))
        
        dlg = ft.AlertDialog(
            modal=True, 
            bgcolor=BG_CONTAINER,
            title=ft.Text("🚨 КРИТИЧНО!" if sys_in_target else "Внимание!", color="#F87171" if sys_in_target else TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
            content=ft.Text(f"Ще изтриете {target_count} файла!{' (СИСТЕМНИ ФАЙЛОВЕ ОТКРИТИ)' if sys_in_target else ''}", color=TEXT_PRIMARY),
            actions=[
                ft.TextButton("Отказ", on_click=close_dlg, style=ft.ButtonStyle(color=TEXT_SECONDARY)), 
                ft.TextButton(f"Да, изтрий {target_count}", on_click=do_delete, style=ft.ButtonStyle(color=BTN_DELETE, bgcolor="#450a0a"))
            ],
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def create_file_row(file_name, full_path, size, f_date, is_sys):
        file_color = "#FCA5A5" if is_sys else TEXT_PRIMARY
        
        # --- НОВО: УМНИ ИКОНКИ (Smart File Icons) ---
        ext = os.path.splitext(file_name)[1].lower()
        if is_sys: icon = "⚙️"
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg']: icon = "🖼️"
        elif ext in ['.mp4', '.avi', '.mkv', '.mov']: icon = "🎬"
        elif ext in ['.mp3', '.wav', '.flac']: icon = "🎵"
        elif ext in ['.pdf']: icon = "📕"
        elif ext in ['.txt', '.doc', '.docx']: icon = "📝"
        elif ext in ['.csv', '.xls', '.xlsx']: icon = "📊"
        elif ext in ['.zip', '.rar', '.7z', '.tar']: icon = "📦"
        elif ext in ['.py', '.js', '.html', '.css', '.json', '.cpp']: icon = "💻"
        else: icon = "📄"
        
        row = ft.Row(spacing=10, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        date_str = f_date.strftime("%d/%m/%Y")
        
        def on_checkbox_change(e):
            if e.control.value: selected_files.add(full_path)
            else: selected_files.discard(full_path)
            update_dynamic_buttons()
            
        cb = ft.Checkbox(value=full_path in selected_files, on_change=on_checkbox_change, fill_color=ACCENT_BLUE)
        lbl_name = ft.Text(f"{icon} {file_name}", color=file_color, size=13, expand=True, tooltip=full_path, no_wrap=True)
        lbl_size = ft.Text(format_size(size), color=TEXT_SECONDARY, size=12, width=70, text_align=ft.TextAlign.RIGHT)
        lbl_date = ft.Text(date_str, color=TEXT_SECONDARY, size=12, width=80, text_align=ft.TextAlign.RIGHT)
        
        icons_group = ft.Row(spacing=0, visible=False)
        active_icon_rows.append(icons_group) 
        
        def on_hover(e):
            if len(selected_files) == 0:  
                icons_group.visible = (e.data == "true")
            row_container.bgcolor = BG_HOVER if e.data == "true" else ft.colors.TRANSPARENT
            row_container.update()

        row_container = ft.Container(content=row, on_hover=on_hover, padding=ft.padding.only(left=5, right=5, top=2, bottom=2), border_radius=6, animate=ft.animation.Animation(150, "easeOut"))

        # --- НОВО: Бутон за Отваряне (Open File) ---
        btn_open = ft.IconButton(ft.icons.OPEN_IN_NEW, icon_size=15, width=26, height=26, padding=0, tooltip="Отвори файла", icon_color=TEXT_PRIMARY, 
                                 on_click=lambda e: open_system_file(full_path))
        btn_c = ft.IconButton(ft.icons.COPY, icon_size=15, width=26, height=26, padding=0, tooltip="Копирай", icon_color=ACCENT_BLUE, 
                              on_click=lambda e: (single_action.update({"type": "copy", "path": full_path, "row": row_container}), single_action_picker.get_directory_path()))
        btn_cut = ft.IconButton(ft.icons.CUT, icon_size=15, width=26, height=26, padding=0, tooltip="Изрежи", icon_color=BTN_CUT, 
                                on_click=lambda e: prompt_single_cut(full_path, row_container, is_sys))
        btn_del = ft.IconButton(ft.icons.DELETE, icon_size=15, width=26, height=26, padding=0, tooltip="Изтрий", icon_color=BTN_DELETE, 
                                on_click=lambda e: prompt_single_delete(full_path, row_container, is_sys))
        
        # Добавихме btn_open най-отпред
        icons_group.controls = [btn_open, btn_c, btn_cut, btn_del]
        row.controls = [cb, lbl_name, lbl_size, lbl_date, icons_group]
        
        return row_container

    def redraw_tree():
        if not global_root_node[0]: return
        results_list.controls.clear()
        active_icon_rows.clear() 
        ui_count[0] = 0
        limit_reached[0] = False
        
        def sort_files(files_list):
            rev = not sort_asc[0]
            if dd_sort.value == "Размер": files_list.sort(key=lambda x: (x[2], natural_sort_key(x[0])), reverse=rev)
            elif dd_sort.value == "Дата": files_list.sort(key=lambda x: (x[3], natural_sort_key(x[0])), reverse=rev)
            elif dd_sort.value == "Тип": files_list.sort(key=lambda x: (os.path.splitext(x[0])[1].lower(), natural_sort_key(x[0])), reverse=rev)
            else: files_list.sort(key=lambda x: natural_sort_key(x[0]), reverse=rev)

        def build_ui_tree(node, current_path=target_folder[0]):
            elements = []
            sorted_dirs = sorted(node.children.keys(), key=natural_sort_key, reverse=(not sort_asc[0]))
            
            for child_name in sorted_dirs:
                if limit_reached[0]: break 
                child_node = node.children[child_name]
                child_path = os.path.join(current_path, child_name)
                
                child_ui_elements = build_ui_tree(child_node, child_path)
                
                if not child_ui_elements:
                    child_ui_elements.append(ft.Text(" (Празна)", color=TEXT_SECONDARY, italic=True, size=11))
                
                def get_all_files(n):
                    res = [f[1] for f in n.files]
                    for c in n.children.values(): res.extend(get_all_files(c))
                    return res
                    
                paths_in_folder = get_all_files(child_node)
                all_selected = all(p in selected_files for p in paths_in_folder) if paths_in_folder else False
                
                def on_folder_cb_change(e, paths=paths_in_folder):
                    if e.control.value:
                        for p in paths: selected_files.add(p)
                    else:
                        for p in paths: selected_files.discard(p)
                    update_dynamic_buttons()
                    redraw_tree() 
                    
                folder_cb = ft.Checkbox(value=all_selected, on_change=on_folder_cb_change, fill_color=ACCENT_BLUE) if paths_in_folder else None
                is_expanded = child_path in expanded_dirs
                
                def make_toggle(cp):
                    def toggle(expanded):
                        if expanded: expanded_dirs.add(cp)
                        else: expanded_dirs.discard(cp)
                    return toggle

                elements.append(CollapsibleDirectory(
                    child_name, 
                    child_ui_elements, 
                    auto_expand=is_expanded, 
                    folder_checkbox=folder_cb,
                    on_toggle_expand=make_toggle(child_path) 
                ))
                    
            sort_files(node.files)
            for file_name, full_path, size, f_date, is_sys in node.files:
                if ui_count[0] >= MAX_UI_FILES:
                    if not limit_reached[0]:
                        elements.append(ft.Text(f"⚠️ Още {len(matched_files) - MAX_UI_FILES} скрити файла.", color="#F59E0B", italic=True, size=12))
                        limit_reached[0] = True
                    break
                ui_count[0] += 1
                elements.append(create_file_row(file_name, full_path, size, f_date, is_sys))
            return elements

        # Ако няма файлове, показваме празно съобщение, иначе рисуваме дървото
        if len(matched_files) == 0:
            results_list.controls = [empty_state]
        else:
            results_list.controls = build_ui_tree(global_root_node[0])
            
        update_summary_text()

    def do_scan(e):
        date_format = "%d/%m/%Y"
        try:
            start_date_obj = datetime.strptime(tf_start.value, date_format)
            end_date_obj = datetime.strptime(tf_end.value, date_format)
        except ValueError:
            show_snack("Грешка: Невалиден формат на датата!", BTN_DELETE)
            return

        start_date = datetime.combine(start_date_obj, time.min)
        end_date = datetime.combine(end_date_obj, time.max)
        raw_exts = [x.strip().lower() for x in tf_ext.value.split(',')] if tf_ext.value else []
        valid_exts = [ext if ext.startswith('.') else f".{ext}" for ext in raw_exts if ext]

        matched_files.clear()
        selected_files.clear() 
        expanded_dirs.clear() 
        
        btn_scan.disabled = True
        progress_ring.visible = True
        lbl_summary.value = f"Сканиране на: {target_folder[0]}..."
        page.update()

        root_node, files, _, has_sys = scan_directory(target_folder[0], start_date, end_date, valid_exts)
        
        matched_files.extend(files)
        has_system_files[0] = has_sys
        global_root_node[0] = root_node
        auto_expand_all[0] = len(matched_files) < 30
        
        if auto_expand_all[0]:
            def pop_expanded(n, p):
                for c_name, c_node in n.children.items():
                    cp = os.path.join(p, c_name)
                    expanded_dirs.add(cp)
                    pop_expanded(c_node, cp)
            pop_expanded(global_root_node[0], target_folder[0])
        
        redraw_tree() 
        
        btn_scan.disabled = False
        progress_ring.visible = False
        page.update()

    # ==============================================================
    # 3. СВЪРЗВАНЕ НА БУТОНИТЕ
    # ==============================================================
    btn_select_folder.on_click = lambda _: scan_picker.get_directory_path()
    btn_scan.on_click = do_scan
    
    def toggle_sort_dir(e):
        sort_asc[0] = not sort_asc[0]
        btn_sort_dir.icon = ft.icons.ARROW_UPWARD if sort_asc[0] else ft.icons.ARROW_DOWNWARD
        redraw_tree()
        
    dd_sort.on_change = lambda _: redraw_tree()
    btn_sort_dir.on_click = toggle_sort_dir

    btn_copy.on_click = lambda _: copy_picker.get_directory_path()
    btn_cut_bulk.on_click = lambda _: cut_bulk_picker.get_directory_path()
    btn_export.on_click = lambda _: export_picker.save_file(allowed_extensions=["txt", "csv"], file_name="Search_Report.txt")
    btn_delete.on_click = lambda _: confirm_bulk_delete_dialog()

    quick_dates_row = ft.Row([
        ft.TextButton("Днес", on_click=lambda _: set_quick_date(0), style=ft.ButtonStyle(color=ACCENT_BLUE)),
        ft.TextButton("7 дни", on_click=lambda _: set_quick_date(7), style=ft.ButtonStyle(color=ACCENT_BLUE)),
        ft.TextButton("Месец", on_click=lambda _: set_quick_date(0, month_start=True), style=ft.ButtonStyle(color=ACCENT_BLUE)),
        ft.TextButton("Година", on_click=lambda _: set_quick_date(0, year_start=True), style=ft.ButtonStyle(color=ACCENT_BLUE)),
    ], wrap=True, width=260, spacing=0)

    # --- СКРИТИ ФИЛТРИ (ExpansionTile) ---
    advanced_filters = ft.ExpansionTile(
        title=ft.Text("Допълнителни филтри", color=TEXT_PRIMARY, size=13, weight="bold"),
        icon_color=ACCENT_BLUE,
        collapsed_text_color=TEXT_SECONDARY,
        controls_padding=ft.padding.only(left=10, right=10, bottom=10),
        controls=[
            quick_dates_row,
            ft.Row([tf_start, tf_end], spacing=10),
            ft.Container(height=10),
            tf_ext,
        ]
    )

    # --- ПЛАВАЩА ЛЕНТА (Toolbar) ---
    toolbar = ft.Container(
        content=ft.Row([btn_copy, btn_cut_bulk, btn_export, btn_delete], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
        bgcolor=BG_SIDEBAR,
        padding=10,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
        margin=ft.padding.only(top=10)
    )

    # ==============================================================
    # 4. РЕДЕНЕ НА ЕКРАНА (UI LAYOUT)
    # ==============================================================
    left_panel = ft.Container(
        width=300, 
        padding=25,
        bgcolor=BG_SIDEBAR,
        border=ft.border.only(right=ft.border.BorderSide(1, BORDER_COLOR)),
        content=ft.Column([
            ft.Row([ft.Icon(ft.icons.ROCKET_LAUNCH, color=ACCENT_BLUE), ft.Text("Smart Manager", size=22, weight="bold", color=TEXT_PRIMARY)]),
            ft.Divider(color=BORDER_COLOR, height=30),
            btn_select_folder,
            ft.Container(height=5),
            lbl_folder,
            ft.Divider(color=BORDER_COLOR, height=30),
            advanced_filters,
            ft.Divider(color=ft.colors.TRANSPARENT, height=15),
            btn_scan,
            ft.Row([progress_ring], alignment=ft.MainAxisAlignment.CENTER)
        ], scroll=ft.ScrollMode.AUTO)
    )

    right_panel = ft.Container(
        expand=True, 
        padding=ft.padding.only(left=25, top=20, right=25, bottom=20),
        content=ft.Column([
            ft.Row([
                ft.Text("Резултати от сканирането", size=22, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                ft.Container(expand=True), 
                ft.Text("Подреди по:", color=TEXT_SECONDARY, size=13),
                dd_sort,
                btn_sort_dir
            ], alignment=ft.MainAxisAlignment.START),
            lbl_summary,
            results_container,
            toolbar
        ])
    )

    page.add(
        ft.Row([left_panel, right_panel], expand=True, spacing=0) 
    )

ft.app(target=main)