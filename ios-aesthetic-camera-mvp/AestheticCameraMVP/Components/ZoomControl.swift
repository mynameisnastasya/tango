import SwiftUI

struct ZoomControl: View {
    let options: [CGFloat]
    let selected: CGFloat
    let onSelect: (CGFloat) -> Void

    var body: some View {
        HStack(spacing: 8) {
            ForEach(options, id: \.self) { value in
                Button(value == 0.5 ? "0.5x" : "\(Int(value))x") { onSelect(value) }
                    .font(.caption.bold())
                    .foregroundStyle(.white)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(Color.black.opacity(selected == value ? 0.62 : 0.32), in: Capsule())
            }
        }
    }
}
