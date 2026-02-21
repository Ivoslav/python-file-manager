import flet as ft
import os
from datetime import datetime, time, timedelta

# ИМПОРТИРАМЕ НАШИТЕ СОБСТВЕНИ МОДУЛИ
from utils import MAX_UI_FILES, natural_sort_key, format_size
from ui_components import CollapsibleDirectory
from operations import (
    scan_directory, copy_single_file, cut_single_file, delete_single_file,
    batch_copy, batch_cut, batch_delete, generate_export_report
)

def main(page: ft.Page):
    page.title = "Търсачка за Файлове v11.0 (MVC Architecture)"
    page.theme_mode = ft.ThemeMode.DARK  
    
    page.window.width = 1000 
    page.window.height = 750
    page.padding = 30
    page.update()

    # --- ГЛОБАЛНИ СЪСТОЯНИЯ ---
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

    # --- ПОМОЩНИ ФУНКЦИИ ЗА UI ---
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
            
        for icon_row in active_icon_rows: icon_row.visible = not is_multi_select
            
        btn_copy.disabled = btn_cut_bulk.disabled = btn_export.disabled = btn_delete.disabled = len(matched_files) == 0
        page.update()

    def update_summary_text():
        total_size = sum(f_size for _, f_size, _, _ in matched_files)
        lbl_summary.value = f"✅ Общо намерени: {len(matched_files)} файла (Размер: {format_size(total_size)})"
        
        if has_system_files[0]:
            lbl_summary.value += " | ⚠️ Има системни файлове!"
            lbl_summary.color = ft.colors.AMBER_400
        else:
            lbl_summary.color = ft.colors.GREEN_ACCENT_200
            
        if limit_reached[0]: lbl_summary.value += f" | ⚡ Показани първите {MAX_UI_FILES}."
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
        page.snack_bar = ft.SnackBar(ft.Text(text, color=ft.colors.WHITE), bgcolor=color)
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

    # --- ПИКЪРИ (FILE PICKERS) ---
    def on_scan_folder_selected(e: ft.FilePickerResultEvent):
        if e.path:
            target_folder[0] = e.path
            lbl_folder.value = f"Избрана: {e.path}"
            page.update()

    def on_copy_folder_selected(e: ft.FilePickerResultEvent):
        if e.path:
            files_to_process = [f[0] for f in matched_files if f[0] in selected_files] if selected_files else [f[0] for f in matched_files]
            count, err_count = batch_copy(files_to_process, e.path, target_folder[0])
            msg = f"Успешно копирани {count} файла."
            if err_count > 0: msg += f" (Грешки: {err_count})"
            show_snack(msg, ft.colors.GREEN_400 if err_count == 0 else ft.colors.ORANGE_400)

    def on_cut_folder_selected(e: ft.FilePickerResultEvent):
        if e.path:
            files_to_process = [f[0] for f in matched_files if f[0] in selected_files] if selected_files else [f[0] for f in matched_files]
            count, err_count, success_files = batch_cut(files_to_process, e.path, target_folder[0])
            
            for f_path in success_files: remove_file_from_state(f_path, None) 
            msg = f"Успешно изрязани {count} файла."
            if err_count > 0: msg += f" Възникнаха {err_count} грешки!"
            show_snack(msg, ft.colors.GREEN_400 if err_count == 0 else ft.colors.ORANGE_400)
            redraw_tree() 
            page.update()

    def on_export_report_selected(e: ft.FilePickerResultEvent):
        if e.path:
            try:
                generate_export_report(e.path, matched_files, selected_files, target_folder[0])
                show_snack("Списъкът е запазен успешно.", ft.colors.GREEN_400)
            except Exception as ex: show_snack(f"Грешка: {ex}", ft.colors.RED_400)

    def on_single_action_selected(e: ft.FilePickerResultEvent):
        if e.path and single_action["path"]:
            try:
                if single_action["type"] == "copy":
                    if copy_single_file(single_action["path"], e.path):
                        show_snack(f"Копиран в: {e.path}", ft.colors.GREEN_400)
                    else: show_snack("Източникът и дестинацията съвпадат!", ft.colors.AMBER_400)
                elif single_action["type"] == "cut":
                    if cut_single_file(single_action["path"], e.path):
                        show_snack(f"Изрязан и преместен в: {e.path}", ft.colors.GREEN_400)
                        remove_file_from_state(single_action["path"], single_action["row"])
                    else: show_snack("Източникът и дестинацията съвпадат!", ft.colors.AMBER_400)
            except Exception as ex: show_snack(f"Грешка: {ex}", ft.colors.RED_400)

    scan_picker = ft.FilePicker(on_result=on_scan_folder_selected)
    copy_picker = ft.FilePicker(on_result=on_copy_folder_selected)
    cut_bulk_picker = ft.FilePicker(on_result=on_cut_folder_selected) 
    export_picker = ft.FilePicker(on_result=on_export_report_selected)
    single_action_picker = ft.FilePicker(on_result=on_single_action_selected)
    page.overlay.extend([scan_picker, copy_picker, cut_bulk_picker, export_picker, single_action_picker])

    dlg_single_delete = ft.AlertDialog(modal=True)

    def prompt_single_delete(path, row_control, is_sys):
        def close_single_dlg(e):
            dlg_single_delete.open = False
            page.update()

        def execute_single_delete(e):
            dlg_single_delete.open = False
            try:
                if delete_single_file(path):
                    show_snack("Файлът беше изтрит завинаги.", ft.colors.RED_400)
                    remove_file_from_state(path, row_control)
            except Exception as ex: show_snack(f"Грешка: {ex}", ft.colors.RED_400)

        dlg_single_delete.title = ft.Text("🚨 Системен файл!" if is_sys else "Потвърждение", color=ft.colors.RED_ACCENT_400 if is_sys else ft.colors.WHITE, weight=ft.FontWeight.BOLD)
        content_text = f"Изтриване на:\n{os.path.basename(path)}?"
        if is_sys: content_text += "\n\nТова е системен файл. Изтриването му е опасно!"
        dlg_single_delete.content = ft.Text(content_text)
        dlg_single_delete.actions = [
            ft.TextButton("Отказ", on_click=close_single_dlg),
            ft.TextButton("Да, изтрий", on_click=execute_single_delete, style=ft.ButtonStyle(color=ft.colors.RED))
        ]
        dlg_single_delete.actions_alignment = ft.MainAxisAlignment.END
        page.dialog = dlg_single_delete
        dlg_single_delete.open = True
        page.update()

    # --- UI КОМПОНЕНТИ ---
    title = ft.Text("Управление на Файлове Pro", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_400)
    btn_select_folder = ft.ElevatedButton("📂 Избери папка", on_click=lambda _: scan_picker.get_directory_path())
    lbl_folder = ft.Text("Избрана: Текуща (.)", color=ft.colors.GREY_400, italic=True)
    
    quick_dates_row = ft.Row([
        ft.Text("Бърз избор:", color=ft.colors.GREY_400),
        ft.TextButton("Днес", on_click=lambda _: set_quick_date(0)),
        ft.TextButton("Последни 7 дни", on_click=lambda _: set_quick_date(7)),
        ft.TextButton("Този месец", on_click=lambda _: set_quick_date(0, month_start=True)),
        ft.TextButton("Тази година", on_click=lambda _: set_quick_date(0, year_start=True)),
    ])

    tf_start = ft.TextField(label="От дата (ДД/ММ/ГГГГ)", value="01/01/2024", width=180, border_color=ft.colors.BLUE_400)
    tf_end = ft.TextField(label="До дата (ДД/ММ/ГГГГ)", value=datetime.now().strftime("%d/%m/%Y"), width=180, border_color=ft.colors.BLUE_400)
    tf_ext = ft.TextField(label="Разширения (txt, pdf)", hint_text="Оставете празно", width=200, border_color=ft.colors.AMBER_600)

    def toggle_sort_dir(e):
        sort_asc[0] = not sort_asc[0]
        btn_sort_dir.icon = ft.icons.ARROW_UPWARD if sort_asc[0] else ft.icons.ARROW_DOWNWARD
        redraw_tree()

    dd_sort = ft.Dropdown(
        value="Име",
        options=[ft.dropdown.Option("Име"), ft.dropdown.Option("Размер"), ft.dropdown.Option("Дата"), ft.dropdown.Option("Тип")],
        width=130, height=45, text_size=13, on_change=lambda _: redraw_tree(), border_color=ft.colors.BLUE_GREY_600
    )
    
    btn_sort_dir = ft.IconButton(icon=ft.icons.ARROW_UPWARD, tooltip="Посока", icon_color=ft.colors.BLUE_400, on_click=toggle_sort_dir)
    progress_ring = ft.ProgressRing(width=24, height=24, stroke_width=3, visible=False)
    results_list = ft.ListView(expand=True, spacing=5, auto_scroll=False)
    results_container = ft.Container(content=results_list, height=300, border=ft.border.all(1, ft.colors.GREY_800), bgcolor=ft.colors.BLACK, padding=10, border_radius=5)
    lbl_summary = ft.Text("Готовност за сканиране...", color=ft.colors.GREEN_ACCENT_200, font_family="monospace")

    btn_scan = ft.ElevatedButton("🔍 Сканирай", width=150, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE)
    
    btn_copy = ft.ElevatedButton("📁 Копирай Всички", disabled=True, color=ft.colors.WHITE, bgcolor=ft.colors.GREEN_700, on_click=lambda _: copy_picker.get_directory_path())
    btn_cut_bulk = ft.ElevatedButton("✂️ Изрежи Всички", disabled=True, color=ft.colors.WHITE, bgcolor=ft.colors.ORANGE_700, on_click=lambda _: cut_bulk_picker.get_directory_path())
    btn_export = ft.ElevatedButton("📄 Експорт Всички", disabled=True, color=ft.colors.WHITE, bgcolor=ft.colors.BLUE_GREY_700, on_click=lambda _: export_picker.save_file(allowed_extensions=["txt", "csv"], file_name="Search_Report.txt"))
    btn_delete = ft.ElevatedButton("🗑️ Изтрий Всички", disabled=True, color=ft.colors.WHITE, bgcolor=ft.colors.RED_700)

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
            show_snack(msg, ft.colors.RED_400 if err_count == 0 else ft.colors.ORANGE_400)
            redraw_tree() 
            page.update()
        
        target_count = len(selected_files) if selected_files else len(matched_files)
        sys_in_target = any(is_sys for f_path, _, _, is_sys in matched_files if (not selected_files or f_path in selected_files))
        
        dlg = ft.AlertDialog(
            modal=True, 
            title=ft.Text("🚨 КРИТИЧНО!" if sys_in_target else "Внимание!", color=ft.colors.RED_ACCENT_400 if sys_in_target else ft.colors.WHITE, weight=ft.FontWeight.BOLD),
            content=ft.Text(f"Ще изтриете {target_count} файла!{' (СИСТЕМНИ ФАЙЛОВЕ ОТКРИТИ)' if sys_in_target else ''}"),
            actions=[ft.TextButton("Отказ", on_click=close_dlg), ft.TextButton(f"Да, изтрий {target_count}", on_click=do_delete, style=ft.ButtonStyle(color=ft.colors.RED))],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    btn_delete.on_click = lambda _: confirm_bulk_delete_dialog()

    # --- ИЗГРАЖДАНЕ НА ДЪРВОТО ---
    def create_file_row(file_name, full_path, size, f_date, is_sys):
        file_color = ft.colors.AMBER_400 if is_sys else ft.colors.GREEN_ACCENT_200
        icon = "⚙️" if is_sys else "📄"
        
        row = ft.Row(spacing=5)
        date_str = f_date.strftime("%d/%m/%Y %H:%M")
        
        def on_checkbox_change(e):
            if e.control.value: selected_files.add(full_path)
            else: selected_files.discard(full_path)
            update_dynamic_buttons()
            
        cb = ft.Checkbox(value=full_path in selected_files, on_change=on_checkbox_change, fill_color=ft.colors.BLUE_400)
        lbl = ft.Text(f"{icon} {file_name} ({format_size(size)})", color=file_color, font_family="monospace", size=13, expand=True, tooltip=f"Дата: {date_str}")
        
        btn_c = ft.IconButton(ft.icons.COPY, icon_size=16, width=25, height=25, padding=0, tooltip="Копирай", icon_color=ft.colors.BLUE_300, 
                              on_click=lambda e: (single_action.update({"type": "copy", "path": full_path, "row": row}), single_action_picker.get_directory_path()))
        btn_cut = ft.IconButton(ft.icons.CUT, icon_size=16, width=25, height=25, padding=0, tooltip="Изрежи", icon_color=ft.colors.ORANGE_300, 
                                on_click=lambda e: (single_action.update({"type": "cut", "path": full_path, "row": row}), single_action_picker.get_directory_path()))
        btn_del = ft.IconButton(ft.icons.DELETE, icon_size=16, width=25, height=25, padding=0, tooltip="Изтрий", icon_color=ft.colors.RED_400, 
                                on_click=lambda e: prompt_single_delete(full_path, row, is_sys))
        
        icons_group = ft.Row([btn_c, btn_cut, btn_del], spacing=0)
        active_icon_rows.append(icons_group) 
        icons_group.visible = (len(selected_files) == 0)

        row.controls = [cb, lbl, icons_group]
        return row

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

        def build_ui_tree(node):
            elements = []
            sorted_dirs = sorted(node.children.keys(), key=natural_sort_key, reverse=(not sort_asc[0]))
            for child_name in sorted_dirs:
                if limit_reached[0]: break 
                child_node = node.children[child_name]
                child_ui_elements = build_ui_tree(child_node)
                if child_ui_elements:
                    elements.append(CollapsibleDirectory(child_name, child_ui_elements, auto_expand_all[0]))
                    
            sort_files(node.files)
            for file_name, full_path, size, f_date, is_sys in node.files:
                if ui_count[0] >= MAX_UI_FILES:
                    if not limit_reached[0]:
                        elements.append(ft.Text(f"⚠️ ... и още {len(matched_files) - MAX_UI_FILES} скрити.", color=ft.colors.ORANGE_400, italic=True))
                        limit_reached[0] = True
                    break
                ui_count[0] += 1
                elements.append(create_file_row(file_name, full_path, size, f_date, is_sys))
            return elements

        results_list.controls = build_ui_tree(global_root_node[0])
        update_summary_text()

    # --- ГЛАВНА ЛОГИКА ЗА СКАНИРАНЕ ---
    def do_scan(e):
        date_format = "%d/%m/%Y"
        try:
            start_date_obj = datetime.strptime(tf_start.value, date_format)
            end_date_obj = datetime.strptime(tf_end.value, date_format)
        except ValueError:
            show_snack("Грешка: Невалиден формат на датата!", ft.colors.RED)
            return

        start_date = datetime.combine(start_date_obj, time.min)
        end_date = datetime.combine(end_date_obj, time.max)
        raw_exts = [x.strip().lower() for x in tf_ext.value.split(',')] if tf_ext.value else []
        valid_exts = [ext if ext.startswith('.') else f".{ext}" for ext in raw_exts if ext]

        matched_files.clear()
        selected_files.clear() 
        
        btn_scan.disabled = True
        progress_ring.visible = True
        lbl_summary.value = f"Сканиране на: {target_folder[0]}... Моля изчакайте."
        lbl_summary.color = ft.colors.GREEN_ACCENT_200
        page.update()

        # МАГИЯТА: Викаме тежката логика от operations.py
        root_node, files, _, has_sys = scan_directory(target_folder[0], start_date, end_date, valid_exts)
        
        matched_files.extend(files)
        has_system_files[0] = has_sys
        global_root_node[0] = root_node
        auto_expand_all[0] = len(matched_files) < 30
        
        redraw_tree() 
        
        btn_scan.disabled = False
        progress_ring.visible = False
        page.update()

    btn_scan.on_click = do_scan

    # --- РЕДЕНЕ НА ЕКРАНА ---
    page.add(
        title,
        ft.Divider(height=10, color=ft.colors.TRANSPARENT),
        ft.Row([btn_select_folder, lbl_folder], alignment=ft.MainAxisAlignment.START),
        quick_dates_row,
        ft.Row([tf_start, tf_end, tf_ext], alignment=ft.MainAxisAlignment.START),
        ft.Divider(height=10, color=ft.colors.TRANSPARENT),
        
        ft.Row([btn_scan, progress_ring, ft.Container(expand=True), ft.Text("Сортиране:", color=ft.colors.GREY_400), dd_sort, btn_sort_dir], alignment=ft.MainAxisAlignment.START),
        
        results_container,
        lbl_summary,
        
        ft.Row([btn_copy, btn_cut_bulk, btn_export, btn_delete], alignment=ft.MainAxisAlignment.START, wrap=True)
    )

ft.app(target=main)