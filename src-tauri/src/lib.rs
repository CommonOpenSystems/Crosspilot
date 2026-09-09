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
                            let _ = window.center();
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
