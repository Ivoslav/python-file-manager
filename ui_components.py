import flet as ft

class CollapsibleDirectory(ft.Column):
    def __init__(self, dir_name, content_controls, auto_expand=False, folder_checkbox=None):
        super().__init__()
        self.spacing = 0 
        self.dir_name = dir_name
        self.is_expanded = auto_expand

        self.icon_btn = ft.IconButton(
            icon=ft.icons.KEYBOARD_ARROW_DOWN if auto_expand else ft.icons.KEYBOARD_ARROW_RIGHT,
            icon_color=ft.colors.BLUE_400,
            icon_size=20,
            on_click=self.toggle_expand,
            width=30, height=30, 
            padding=0
        )
        
        self.dir_label = ft.Text(f"📂 {self.dir_name}", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)
        
        self.files_container = ft.Container(
            content=ft.Column(controls=content_controls, spacing=0),
            visible=self.is_expanded,
            padding=ft.padding.only(left=24) 
        )

        # НОВО: Подреждаме елементите -> Бутон за сгъване, Чекбокс (ако има), Име
        row_controls = [self.icon_btn]
        if folder_checkbox:
            row_controls.append(folder_checkbox)
        row_controls.append(self.dir_label)

        self.controls = [
            ft.Row(row_controls, spacing=0),
            self.files_container
        ]

    def toggle_expand(self, e):
        self.is_expanded = not self.is_expanded
        self.files_container.visible = self.is_expanded
        self.icon_btn.icon = ft.icons.KEYBOARD_ARROW_DOWN if self.is_expanded else ft.icons.KEYBOARD_ARROW_RIGHT
        self.update()