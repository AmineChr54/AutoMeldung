import flet as ft
from gui.utils.settings import save_settings

def create_export_section(page: ft.Page, settings: dict):
    # Picker
    export_dir_picker = ft.FilePicker()
    page.overlay.append(export_dir_picker)

    # Fields
    export_folder = ft.TextField(label="Export Folder", read_only=True, expand=True, value=settings.get("export_folder", ""))
    limit_rows = ft.TextField(label="Limit rows", value=str(settings.get("limit_rows", "20")), width=120, keyboard_type=ft.KeyboardType.NUMBER)
    creation_date_input = ft.TextField(label="Creation Date (DD.MM.YYYY)", hint_text="Leave empty for today", expand=True, value=settings.get("creation_date", ""))

    # Handlers
    def on_export_dir_pick(e: ft.FilePickerResultEvent):
        if e.path:
            export_folder.value = e.path
            export_folder.update()
            settings["export_folder"] = export_folder.value
            save_settings(settings)

    def on_limit_change(e):
        val = limit_rows.value.strip()
        if not val.isdigit():
            return
        settings["limit_rows"] = int(val)
        save_settings(settings)

    def on_creation_date_change(e):
        settings["creation_date"] = creation_date_input.value
        save_settings(settings)

    export_dir_picker.on_result = on_export_dir_pick
    limit_rows.on_change = on_limit_change
    creation_date_input.on_change = on_creation_date_change

    # Layout
    export_card = ft.Card(
        content=ft.Container(
            content=ft.ExpansionTile(
                title=ft.Text("Export Options", style=ft.TextThemeStyle.TITLE_MEDIUM),
                initially_expanded=False,
                controls=[
                    ft.Column(
                        controls=[
                            ft.Row([
                                export_folder,
                                ft.ElevatedButton(
                                    "Select Folder", icon=ft.Icons.FOLDER_OPEN,
                                    on_click=lambda e: export_dir_picker.get_directory_path()
                                ),
                            ]),
                            ft.Row([
                                creation_date_input,
                                limit_rows,
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ],
                        spacing=12,
                    )
                ]
            ),
            padding=16,
        )
    )

    refs = {
        "export_folder": export_folder,
        "limit_rows": limit_rows,
        "creation_date_input": creation_date_input,
    }

    return export_card, refs
