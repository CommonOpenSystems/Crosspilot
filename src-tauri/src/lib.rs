use tauri::Manager;
use tauri::Emitter;
use tauri_plugin_global_shortcut::{Code, GlobalShortcutExt, Modifiers, Shortcut, ShortcutEvent, ShortcutState};

// Change these two lines to remap the shortcut
const SHORTCUT_MODIFIERS: Modifiers = Modifiers::SUPER.union(Modifiers::ALT);
const SHORTCUT_CODE: Code = Code::KeyK;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let shortcut = Shortcut::new(Some(SHORTCUT_MODIFIERS), SHORTCUT_CODE);

    tauri::Builder::default()
        .plugin(
            tauri_plugin_global_shortcut::Builder::new()
                .with_handler(move |app, _s, event: ShortcutEvent| {
                    if event.state == ShortcutState::Pressed {
                        let Some(window) = app.get_webview_window("main") else { return };
                        if window.is_visible().unwrap_or(false) {
                            let _ = app.emit("crosspilot://hide", ());
                            let _ = window.hide();
                        } else {
                            if let Ok(Some(monitor)) = window.current_monitor()
                                .or_else(|_| window.primary_monitor())
                            {
                                let screen = monitor.size();
                                let scale = monitor.scale_factor();
                                let win_w = (380.0 * scale) as u32;
                                let win_h = (520.0 * scale) as u32;
                                let margin = (16.0 * scale) as u32;
                                let x = (screen.width.saturating_sub(win_w + margin)) as i32;
                                let y = (screen.height.saturating_sub(win_h + margin)) as i32;
                                let _ = window.set_size(tauri::Size::Physical(tauri::PhysicalSize { width: win_w, height: win_h }));
                                let _ = window.set_position(tauri::Position::Physical(tauri::PhysicalPosition { x, y }));
                            }
                            let _ = window.show();
                            let _ = window.set_focus();
                            #[cfg(target_os = "macos")]
                            {
                                let pid = std::process::id();
                                let script = format!(
                                    "tell application \"System Events\" to set frontmost of the first process whose unix id is {} to true",
                                    pid
                                );
                                let _ = std::process::Command::new("osascript")
                                    .args(["-e", &script])
                                    .spawn();
                            }
                            #[cfg(target_os = "linux")]
                            {
                                let pid = std::process::id();
                                let _ = std::process::Command::new("xdotool")
                                    .args(["search", "--pid", &pid.to_string(),
                                           "windowactivate", "--sync"])
                                    .spawn();
                            }
                            let _ = app.emit("crosspilot://show", ());
                        }
                    }
                })
                .build(),
        )
        .setup(move |app| {
            app.global_shortcut().register(shortcut)?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
