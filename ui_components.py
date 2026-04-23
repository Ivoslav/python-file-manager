"""
Модул: ui_components.py
Описание: Съдържа дефиниции на персонализирани графични компоненти (Custom Widgets) 
за изграждане на потребителския интерфейс чрез рамката Flet.
"""
import flet as ft

class CollapsibleDirectory(ft.Column):
    """
    Графичен компонент за визуализация на директории в дървовидна структура (Tree View).
    Поддържа автоматично разгъване/свиване, интегрирани интерактивни контроли и 
    визуални водещи линии (Tree Lines) за подобряване на потребителската ориентация.
    """
    def __init__(self, dir_name, content_controls, auto_expand=False, folder_checkbox=None, on_toggle_expand=None):
        """
        Инициализира компонента за директория.
        
        Параметри:
            dir_name (str): Името на директорията за визуализация.
            content_controls (list): Списък от Flet контроли (файлове или поддиректории), които се съдържат в нея.
            auto_expand (bool): Флаг, определящ дали директорията да бъде разгъната по подразбиране.
            folder_checkbox (ft.Control): Опционален компонент (Checkbox/IconButton) за масова селекция.
            on_toggle_expand (callable): Callback функция, която се извиква при промяна на състоянието (разгъване/свиване).
        """
        super().__init__()
        self.spacing = 0 
        self.dir_name = dir_name
        self.is_expanded = auto_expand
        self.on_toggle_expand = on_toggle_expand

        # Контрола за управление на състоянието (Стрелка)
        self.icon_btn = ft.IconButton(
            icon=ft.icons.KEYBOARD_ARROW_DOWN if auto_expand else ft.icons.KEYBOARD_ARROW_RIGHT,
            icon_color=ft.colors.BLUE_400,
            icon_size=20,
            on_click=self.toggle_expand,
            width=30, height=30, 
            padding=0
        )
        
        self.dir_label = ft.Text(f"📂 {self.dir_name}", weight=ft.FontWeight.BOLD, color="#F8FAFC")
        
        # Контейнер за вложеното съдържание с интегрирани визуални водещи линии
        self.files_container = ft.Container(
            content=ft.Column(controls=content_controls, spacing=0),
            visible=self.is_expanded,
            padding=ft.padding.only(left=18), 
            margin=ft.padding.only(left=14),  
            border=ft.border.only(left=ft.border.BorderSide(1, "#252833")) 
        )

        row_controls = [self.icon_btn]
        if folder_checkbox:
            row_controls.append(folder_checkbox)
        row_controls.append(self.dir_label)

        # Контейнер на самата директория с дефиниран ефект при посочване (Hover state)
        folder_row = ft.Container(
            content=ft.Row(row_controls, spacing=0),
            padding=ft.padding.only(top=2, bottom=2, right=5),
            border_radius=6,
            on_hover=lambda e: self.on_folder_hover(e, folder_row),
            animate=ft.animation.Animation(150, "easeOut")
        )

        self.controls = [
            folder_row,
            self.files_container
        ]

    def on_folder_hover(self, e, container):
        """Обработва събитията при преминаване на курсора върху компонента (Hover Event)."""
        container.bgcolor = "#232630" if e.data == "true" else ft.colors.TRANSPARENT
        container.update()

    def toggle_expand(self, e):
        """Превключва състоянието на видимост на вложеното съдържание и обновява иконите."""
        self.is_expanded = not self.is_expanded
        self.files_container.visible = self.is_expanded
        self.icon_btn.icon = ft.icons.KEYBOARD_ARROW_DOWN if self.is_expanded else ft.icons.KEYBOARD_ARROW_RIGHT
        
        if self.on_toggle_expand:
            self.on_toggle_expand(self.is_expanded)
            
        self.update()