import SwiftUI

struct IconBubble: View {
    let systemName: String
    var body: some View {
        Image(systemName: systemName)
            .foregroundStyle(.white)
            .frame(width: 44, height: 44)
            .background(Color.black.opacity(0.35), in: Circle())
    }
}
