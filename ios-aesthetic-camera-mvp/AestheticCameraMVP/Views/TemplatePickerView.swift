import SwiftUI

struct TemplatePickerView: View {
    @Binding var selectedTemplate: CompositionTemplate

    var body: some View {
        List {
            ForEach(TemplateLibrary.categories) { category in
                Section(category.rawValue) {
                    ForEach(TemplateLibrary.templates.filter { $0.category == category }) { template in
                        Button {
                            selectedTemplate = template
                        } label: {
                            VStack(alignment: .leading, spacing: 6) {
                                Text(template.name).font(.headline)
                                Text(template.description).font(.caption).opacity(0.7)
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("Guides")
    }
}
