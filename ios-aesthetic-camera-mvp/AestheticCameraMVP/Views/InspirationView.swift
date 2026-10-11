import SwiftUI

struct InspirationView: View {
    private let tips = [
        ("Coffee", "Shoot near a window, keep one hero cup, add texture and leave empty space."),
        ("Negative space", "Do not fill the whole frame. Empty space makes the photo feel expensive."),
        ("Food", "Use top-down light, one plate as the hero, and small details around it."),
        ("Travel", "Keep the horizon on a third line and add a person or object for scale."),
        ("Outfit", "Step back, keep shoes inside the frame, and align vertical wall lines.")
    ]

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                ForEach(tips, id: \.0) { tip in
                    VStack(alignment: .leading, spacing: 10) {
                        Text(tip.0).font(.title3.bold())
                        Text(tip.1).font(.body).opacity(0.75)
                    }
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(20)
                    .background(LinearGradient(colors: [.black, .gray.opacity(0.55)], startPoint: .topLeading, endPoint: .bottomTrailing), in: RoundedRectangle(cornerRadius: 26))
                }
            }.padding()
        }
        .background(Color.black.ignoresSafeArea())
        .navigationTitle("Inspiration")
    }
}
