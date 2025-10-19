import flet as ft
import os
import sys
import json

# Ensure project root is on sys.path so `import automeldung...` works when running from gui/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main(page: ft.Page):
    # Page setup
    page.title = "Automeldung — PDF Automation"
    page.padding = 8
    page.window.width = 859
    page.window.height = 539
    page.theme_mode = "dark"

    # ----- Settings persistence -----
    SETTINGS_PATH = os.path.join(PROJECT_ROOT, "app_settings.json")

    def load_settings() -> dict:
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_settings(settings: dict):
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except Exception:
            pass

    settings = load_settings()

    # ----- File/Folder pickers -----
    krankmeldungen_picker = ft.FilePicker()
    kontaktdaten_picker = ft.FilePicker()
    krank_ohne_picker = ft.FilePicker()
    krank_mit_picker = ft.FilePicker()
    gesund_picker = ft.FilePicker()
    au_dir_picker = ft.FilePicker()
    export_dir_picker = ft.FilePicker()

    page.overlay.extend([
        krankmeldungen_picker,
        kontaktdaten_picker,
        krank_ohne_picker,
        krank_mit_picker,
        gesund_picker,
        au_dir_picker,
        export_dir_picker,
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
    export_folder = ft.TextField(label="Export Folder", read_only=True, expand=True, value=settings.get("export_folder", ""))

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

    def on_export_dir_pick(e: ft.FilePickerResultEvent):
        if e.path:
            export_folder.value = e.path
            export_folder.update()
            settings["export_folder"] = export_folder.value
            save_settings(settings)

    krankmeldungen_picker.on_result = on_krankmeldungen_pick
    krank_ohne_picker.on_result = on_krank_ohne_pick
    krank_mit_picker.on_result = on_krank_mit_pick
    gesund_picker.on_result = on_gesund_pick
    kontaktdaten_picker.on_result = on_kontaktdaten_pick
    au_dir_picker.on_result = on_au_dir_pick
    export_dir_picker.on_result = on_export_dir_pick

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

    # ----- Options -----
    limit_rows = ft.TextField(label="Limit rows", value=str(settings.get("limit_rows", "20")), width=120, keyboard_type=ft.KeyboardType.NUMBER)

    def on_limit_change(e):
        val = limit_rows.value.strip()
        if not val.isdigit():
            return
        settings["limit_rows"] = int(val)
        save_settings(settings)

    limit_rows.on_change = on_limit_change
    krankmeldungen_sheet_name.on_change = on_krankmeldungen_sheet_change
    kontaktdaten_sheet_name.on_change = on_kontaktdaten_sheet_change

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

    # ----- Status & Actions -----
    log_view = ft.ListView(expand=True, spacing=6, auto_scroll=True)
    status_bar = ft.Text("Ready.")
    prog = ft.ProgressBar(width=400, visible=False)

    def append_log(msg: str):
        log_view.controls.append(ft.Text(msg))
        log_view.update()
        status_bar.value = msg
        status_bar.update()

    # --- Backend wiring (non-invasive) ---
    import threading
    import time
    import importlib
    import automeldung.config as config

    def on_run_clicked(e):
        # Apply UI paths to config temporarily (only if provided)
        if krankmeldungen_path.value:
            config.krankmeldungsliste_path = krankmeldungen_path.value
        # Optional sheet names: apply only if provided, else keep config defaults
        if krankmeldungen_sheet_name.value.strip():
            config.krankmeldungsliste_sheet_name = krankmeldungen_sheet_name.value.strip()
        if export_folder.value:
            config.export_path = export_folder.value
        if krank_ohne_path.value:
            config.vorlage_krankmeldung_ohne_au_path = krank_ohne_path.value
        if krank_mit_path.value:
            config.vorlage_krankmeldung_mit_au_path = krank_mit_path.value
        if gesund_path.value:
            config.vorlage_gesundmeldung_path = gesund_path.value
        if au_folder.value:
            config.au_files_path = au_folder.value
        if kontaktdaten_path.value:
            config.kontaktdaten_path = kontaktdaten_path.value
        if kontaktdaten_sheet_name.value.strip():
            config.kontaktdaten_sheet_name = kontaktdaten_sheet_name.value.strip()

        # Limit rows (best-effort; the exporter currently uses head(20))
        try:
            limit = int(limit_rows.value.strip()) if limit_rows.value.strip() else 20
        except ValueError:
            limit = 20
        os.environ['AUTOMELDUNG_LIMIT'] = str(limit)

        # Persist current values
        settings.update({
            "krankmeldungen_path": krankmeldungen_path.value,
            "krankmeldungen_sheet_name": krankmeldungen_sheet_name.value,
            "krank_ohne_path": krank_ohne_path.value,
            "krank_mit_path": krank_mit_path.value,
            "gesund_path": gesund_path.value,
            "kontaktdaten_path": kontaktdaten_path.value,
            "kontaktdaten_sheet_name": kontaktdaten_sheet_name.value,
            "au_folder": au_folder.value,
            "export_folder": export_folder.value,
            "limit_rows": limit,
        })
        save_settings(settings)

        # Show progress UI
        prog.visible = True
        prog.update()
        append_log("Export started...")

        def worker():
            try:
                # (Re-)set logger so backend logs appear in the UI
                try:
                    config.set_logger(lambda m: append_log(str(m)))
                except Exception:
                    pass
                # Re-import exporter to ensure it sees updated config
                importlib.reload(config)
                try:
                    config.set_logger(lambda m: append_log(str(m)))
                except Exception:
                    pass
                # Run existing exporter (iterates over head(20) inside)
                from automeldung.main_exporter import main_exporter as run_exporter
                run_exporter()
                append_log("Export finished.")
            except Exception as ex:
                append_log(f"Error: {ex}")
            finally:
                prog.visible = False
                page.update()

        threading.Thread(target=worker, daemon=True).start()

    def on_cancel_clicked(e):
        append_log("Operation cancelled.")
        prog.visible = False
        prog.update()

    actions_row = ft.Row([
        ft.ElevatedButton("Run", icon=ft.Icons.PLAY_ARROW, on_click=on_run_clicked),
        ft.OutlinedButton("Cancel", icon=ft.Icons.CANCEL, on_click=on_cancel_clicked),
    ], spacing=12)

    status_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Status", style=ft.TextThemeStyle.TITLE_MEDIUM),
                log_view,
                ft.Row([prog, status_bar], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                actions_row,
            ], spacing=12),
            padding=16,
            expand=True,
        )
    )

    # ----- Layout -----
    header = ft.Row([
        ft.Icon(ft.Icons.DESCRIPTION, color=ft.Colors.BLUE_400),
        ft.Text("Automeldung – PDF Automation", style=ft.TextThemeStyle.HEADLINE_MEDIUM, size=20),
        ft.Container(expand=True),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    content_column = ft.Column(
        controls=[
            header,
            ft.Divider(),
            ft.ResponsiveRow([
                ft.Column([inputs_card], col={'sm': 12, 'md': 12, 'lg': 6}),
                ft.Column([export_card], col={'sm': 12, 'md': 12, 'lg': 6}),
                ft.Column([status_card], col={'sm': 12, 'md': 12, 'lg': 12}),
            ], columns=12, run_spacing=12, spacing=12),
            ft.Container(content=ft.Text("Automeldung", color=ft.Colors.GREY), padding=8, alignment=ft.alignment.center_right),
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

    page.add(content_column)


ft.app(target=main)
