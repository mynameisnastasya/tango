import SwiftUI
import UIKit

struct ResultPreviewView: View {
    let image: UIImage
    let template: CompositionTemplate
    let gridOpacity: Double
    let onRetake: () -> Void
    var body: some View {
        VStack(spacing: 18) {
            Image(uiImage: image).resizable().scaledToFit()
            Text("Preview").font(.headline)
            Button("Retake", action: onRetake)
        }
        .padding()
        .background(Color.black)
    }
}
