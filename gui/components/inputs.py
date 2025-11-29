import flet as ft
from gui.utils.settings import save_settings

def create_inputs_section(page: ft.Page, settings: dict):
    # ----- Pickers -----
    krankmeldungen_picker = ft.FilePicker()
    kontaktdaten_picker = ft.FilePicker()
    krank_ohne_picker = ft.FilePicker()
    krank_mit_picker = ft.FilePicker()
    gesund_picker = ft.FilePicker()
    au_dir_picker = ft.FilePicker()

    page.overlay.extend([
        krankmeldungen_picker,
        kontaktdaten_picker,
        krank_ohne_picker,
        krank_mit_picker,
        gesund_picker,
        au_dir_picker,
    ])

    # ----- Inputs (paths) -----
    krankmeldungen_path = ft.TextField(label="Krankmeldungen (.xlsx)", read_only=True, expand=True, value=settings.get("krankmeldungen_path", ""))
    krankmeldungen_sheet_name = ft.TextField(label="Krankmeldungen Sheet Name", expand=True, value=settings.get("krankmeldungen_sheet_name", ""))
    krank_ohne_path = ft.TextField(label="Krankmeldung Ohne AU Template (.pdf)", read_only=True, expand=True, value=settings.get("krank_ohne_path", ""))
    krank_mit_path = ft.TextField(label="Krankmeldung Mit AU Template (.pdf)", read_only=True, expand=True, value=settings.get("krank_mit_path", ""))
    gesund_path = ft.TextField(label="Gesundmeldung Template (.pdf)", read_only=True, expand=True, value=settings.get("gesund_path", ""))
    kontaktdaten_path = ft.TextField(label="Kontaktdaten (.xlsx)", read_only=True, expand=True, value=settings.get("kontaktdaten_path", ""))
    kontaktdaten_sheet_name = ft.TextField(label="Kontaktdaten Sheet Name", expand=True, value=settings.get("kontaktdaten_sheet_name", ""))
    au_folder = ft.TextField(label="AU Files Folder", read_only=True, expand=True, value=settings.get("au_folder", ""))

    # ----- Handlers -----
    def on_krankmeldungen_pick(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            krankmeldungen_path.value = e.files[0].path or e.files[0].name
            krankmeldungen_path.update()
            settings["krankmeldungen_path"] = krankmeldungen_path.value
            save_settings(settings)

    def on_krank_ohne_pick(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            krank_ohne_path.value = e.files[0].path or e.files[0].name
            krank_ohne_path.update()
            settings["krank_ohne_path"] = krank_ohne_path.value
            save_settings(settings)

    def on_krankmeldungen_sheet_change(e):
        settings["krankmeldungen_sheet_name"] = krankmeldungen_sheet_name.value
        save_settings(settings)

    def on_krank_mit_pick(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            krank_mit_path.value = e.files[0].path or e.files[0].name
            krank_mit_path.update()
            settings["krank_mit_path"] = krank_mit_path.value
            save_settings(settings)

    def on_gesund_pick(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            gesund_path.value = e.files[0].path or e.files[0].name
            gesund_path.update()
            settings["gesund_path"] = gesund_path.value
            save_settings(settings)

    def on_kontaktdaten_pick(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            kontaktdaten_path.value = e.files[0].path or e.files[0].name
            kontaktdaten_path.update()
            settings["kontaktdaten_path"] = kontaktdaten_path.value
            save_settings(settings)

    def on_kontaktdaten_sheet_change(e):
        settings["kontaktdaten_sheet_name"] = kontaktdaten_sheet_name.value
        save_settings(settings)

    def on_au_dir_pick(e: ft.FilePickerResultEvent):
        if e.path:
            au_folder.value = e.path
            au_folder.update()
            settings["au_folder"] = au_folder.value
            save_settings(settings)

    # Wire handlers
    krankmeldungen_picker.on_result = on_krankmeldungen_pick
    krank_ohne_picker.on_result = on_krank_ohne_pick
    krank_mit_picker.on_result = on_krank_mit_pick
    gesund_picker.on_result = on_gesund_pick
    kontaktdaten_picker.on_result = on_kontaktdaten_pick
    au_dir_picker.on_result = on_au_dir_pick
    
    krankmeldungen_sheet_name.on_change = on_krankmeldungen_sheet_change
    kontaktdaten_sheet_name.on_change = on_kontaktdaten_sheet_change

    # ----- Layout -----
    inputs_card = ft.Card(
        content=ft.Container(
            content=ft.ExpansionTile(
                title=ft.Text("Input Files", style=ft.TextThemeStyle.TITLE_MEDIUM),
                initially_expanded=False,
                controls=[
                    ft.Column(
                        controls=[
                            ft.Row([
                                krankmeldungen_path,
                                ft.ElevatedButton(
                                    "Browse", icon=ft.Icons.UPLOAD_FILE,
                                    on_click=lambda e: krankmeldungen_picker.pick_files(allow_multiple=False, allowed_extensions=["xlsx"]) 
                                ),
                            ]),
                            krankmeldungen_sheet_name,
                            ft.Row([
                                kontaktdaten_path,
                                ft.ElevatedButton(
                                    "Browse", icon=ft.Icons.CONTACT_PAGE,
                                    on_click=lambda e: kontaktdaten_picker.pick_files(allow_multiple=False, allowed_extensions=["xlsx"]) 
                                ),
                            ]),
                            kontaktdaten_sheet_name,
                            ft.Row([
                                krank_ohne_path,
                                ft.ElevatedButton(
                                    "Browse", icon=ft.Icons.PICTURE_AS_PDF,
                                    on_click=lambda e: krank_ohne_picker.pick_files(allow_multiple=False, allowed_extensions=["pdf"]) 
                                ),
                            ]),
                            ft.Row([
                                krank_mit_path,
                                ft.ElevatedButton(
                                    "Browse", icon=ft.Icons.PICTURE_AS_PDF,
                                    on_click=lambda e: krank_mit_picker.pick_files(allow_multiple=False, allowed_extensions=["pdf"]) 
                                ),
                            ]),
                            ft.Row([
                                gesund_path,
                                ft.ElevatedButton(
                                    "Browse", icon=ft.Icons.PICTURE_AS_PDF,
                                    on_click=lambda e: gesund_picker.pick_files(allow_multiple=False, allowed_extensions=["pdf"]) 
                                ),
                            ]),
                            ft.Row([
                                au_folder,
                                ft.ElevatedButton(
                                    "Select Folder", icon=ft.Icons.FOLDER_OPEN,
                                    on_click=lambda e: au_dir_picker.get_directory_path()
                                ),
                            ]),
                        ],
                        spacing=12,
                    )
                ]
            ),
            padding=16,
        )
    )

    refs = {
        "krankmeldungen_path": krankmeldungen_path,
        "krankmeldungen_sheet_name": krankmeldungen_sheet_name,
        "krank_ohne_path": krank_ohne_path,
        "krank_mit_path": krank_mit_path,
        "gesund_path": gesund_path,
        "kontaktdaten_path": kontaktdaten_path,
        "kontaktdaten_sheet_name": kontaktdaten_sheet_name,
        "au_folder": au_folder,
    }

    return inputs_card, refs
