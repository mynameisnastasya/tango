import SwiftUI

struct TemplateCard: View {
    let template: CompositionTemplate
    let selected: Bool
    var body: some View {
        VStack(alignment: .leading) {
            Text(template.name).font(.caption.bold())
            Text(template.category.rawValue).font(.caption2).opacity(0.7)
        }
        .foregroundStyle(.white)
        .padding(12)
        .background(Color.black.opacity(selected ? 0.62 : 0.32), in: RoundedRectangle(cornerRadius: 18))
    }
}
