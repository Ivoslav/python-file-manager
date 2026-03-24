import flet as ft

class CollapsibleDirectory(ft.Column):
    def __init__(self, dir_name, content_controls, auto_expand=False, folder_checkbox=None, on_toggle_expand=None):
        super().__init__()
        self.spacing = 0 
        self.dir_name = dir_name
        self.is_expanded = auto_expand
        self.on_toggle_expand = on_toggle_expand

        self.icon_btn = ft.IconButton(
            icon=ft.icons.KEYBOARD_ARROW_DOWN if auto_expand else ft.icons.KEYBOARD_ARROW_RIGHT,
            icon_color=ft.colors.BLUE_400,
            icon_size=20,
            on_click=self.toggle_expand,
            width=30, height=30, 
            padding=0
        )
        
        self.dir_label = ft.Text(f"📂 {self.dir_name}", weight=ft.FontWeight.BOLD, color="#F8FAFC")
        
        # --- МАГИЯТА ЗА ОРИЕНТАЦИЯ: Вертикалните водещи линии (Tree Lines) ---
        self.files_container = ft.Container(
            content=ft.Column(controls=content_controls, spacing=0),
            visible=self.is_expanded,
            # left=18 отдалечава файловете от линията
            padding=ft.padding.only(left=18), 
            # left=14 бута самата линия да се падне точно под центъра на стрелката
            margin=ft.padding.only(left=14),  
            # Чертаем вертикалната линия отляво!
            border=ft.border.only(left=ft.border.BorderSide(1, "#252833")) 
        )

        row_controls = [self.icon_btn]
        if folder_checkbox:
            row_controls.append(folder_checkbox)
        row_controls.append(self.dir_label)

        # Добавяме лек Hover ефект и на самата папка, за да се вижда ясно коя е
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
        # Същият мек цвят като при файловете
        container.bgcolor = "#232630" if e.data == "true" else ft.colors.TRANSPARENT
        container.update()

    def toggle_expand(self, e):
        self.is_expanded = not self.is_expanded
        self.files_container.visible = self.is_expanded
        self.icon_btn.icon = ft.icons.KEYBOARD_ARROW_DOWN if self.is_expanded else ft.icons.KEYBOARD_ARROW_RIGHT
        
        if self.on_toggle_expand:
            self.on_toggle_expand(self.is_expanded)
            
        self.update()