import flet as ft

def create_status_section():
    log_view = ft.ListView(expand=True, spacing=6, auto_scroll=True)
    status_bar = ft.Text("Ready.")
    prog = ft.ProgressBar(width=400, visible=False)

    # State for log grouping
    log_state = {"current_column": None}

    def append_log(msg: str):
        # Colorize based on simple keywords
        m = str(msg)
        ml = m.lower()
        color = None
        if any(k in ml for k in ("error", "fehler", "exception", "traceback")):
            color = ft.Colors.RED_400
        elif any(k in ml for k in ("warn", "achtung")):
            color = ft.Colors.AMBER_400
        elif any(k in ml for k in ("finished", "success", "done", "fertig")):
            color = ft.Colors.GREEN_400
        elif any(k in ml for k in ("started", "starting", "start")):
            color = ft.Colors.BLUE_300
        else:
            color = ft.Colors.GREY

        # Determine if we need a new block
        # "Processing:" indicates start of a new person/row
        # "Export started..." or "Export finished." are major lifecycle events
        is_new_block = m.startswith("Processing:") or m.startswith("Export started") or m.startswith("Export finished")

        if is_new_block or log_state["current_column"] is None:
            log_state["current_column"] = ft.Column(spacing=2)
            container = ft.Container(
                content=log_state["current_column"],
                padding=10,
                border=ft.border.all(1, color if color != ft.Colors.GREY else ft.Colors.BLUE_GREY_400),
                border_radius=5,
            )
            log_view.controls.append(container)
            log_view.update()

        # Add the message line to the current block
        log_state["current_column"].controls.append(ft.Text(m, color=color, selectable=True))
        log_state["current_column"].update()

        status_bar.value = m
        status_bar.color = color
        status_bar.update()

    run_btn = ft.ElevatedButton("Run", icon=ft.Icons.PLAY_ARROW)
    cancel_btn = ft.OutlinedButton("Cancel", icon=ft.Icons.CANCEL)
    
    actions_row = ft.Row([
        run_btn,
        cancel_btn,
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
    
    refs = {
        "append_log": append_log,
        "prog": prog,
        "run_btn": run_btn,
        "cancel_btn": cancel_btn,
    }

    return status_card, refs
