import SwiftUI

struct SettingsView: View {
    @AppStorage("appTheme") private var appTheme = "system"
    @AppStorage("gridOpacity") private var gridOpacity = 0.72

    var body: some View {
        Form {
            Picker("Theme", selection: $appTheme) {
                Text("System").tag("system")
                Text("Dark").tag("dark")
                Text("Light").tag("light")
            }
            Slider(value: $gridOpacity, in: 0.15...1) { Text("Grid opacity") }
            Toggle("Haptic feedback", isOn: .constant(true))
            Toggle("Save original photo", isOn: .constant(true))
            Toggle("Show hints", isOn: .constant(true))
        }
        .navigationTitle("Settings")
    }
}
