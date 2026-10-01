import SwiftUI

final class CameraState: ObservableObject {
    let service = CameraService()
    @Published var selectedTemplate = TemplateLibrary.templates[0]
}
