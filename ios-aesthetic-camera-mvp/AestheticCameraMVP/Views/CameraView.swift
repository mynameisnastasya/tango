import SwiftUI
import AVFoundation

struct CameraScreen: View {
    @StateObject private var camera = CameraService()
    @State private var selectedTemplate = TemplateLibrary.templates[0]
    @State private var photo: UIImage?
    @AppStorage("gridOpacity") private var gridOpacity = 0.72

    var body: some View {
        NavigationStack {
            ZStack {
                CameraPreviewView(session: camera.session).ignoresSafeArea()
                OverlayRenderer(template: selectedTemplate, opacity: gridOpacity).ignoresSafeArea()
                VStack {
                    HStack {
                        Text("Aesthetic Cam").font(.headline).foregroundStyle(.white)
                        Spacer()
                        Button { camera.flashMode = camera.flashMode == .off ? .on : .off } label: { IconBubble(systemName: camera.flashMode == .off ? "bolt.slash" : "bolt.fill") }
                        Button { camera.switchCamera() } label: { IconBubble(systemName: "camera.rotate") }
                        NavigationLink(destination: SettingsView()) { IconBubble(systemName: "slider.horizontal.3") }
                    }
                    Spacer()
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack {
                            ForEach(TemplateLibrary.templates) { template in
                                Button { selectedTemplate = template } label: {
                                    Text(template.name).font(.caption.bold()).foregroundStyle(.white).padding(12).background(Color.black.opacity(template.id == selectedTemplate.id ? 0.65 : 0.32), in: Capsule())
                                }
                            }
                        }
                    }
                    HStack {
                        NavigationLink(destination: InspirationView()) { IconBubble(systemName: "sparkles") }
                        Spacer()
                        Button { Task { photo = try? await camera.capture() } } label: { Circle().fill(Color.white).frame(width: 74, height: 74) }
                        Spacer()
                        NavigationLink(destination: TemplatePickerView(selectedTemplate: $selectedTemplate)) { IconBubble(systemName: "square.grid.2x2") }
                    }
                }.padding(16)
            }
            .task { if await camera.requestPermission() { camera.start() } }
            .sheet(item: Binding(get: { photo.map { CapturedPhoto(image: $0) } }, set: { photo = $0?.image })) { item in
                ResultPreviewView(image: item.image, template: selectedTemplate, gridOpacity: gridOpacity) { photo = nil }
            }
        }
    }
}

struct CapturedPhoto: Identifiable { let id = UUID(); let image: UIImage }
