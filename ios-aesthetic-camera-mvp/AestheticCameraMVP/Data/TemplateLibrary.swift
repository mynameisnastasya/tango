import Foundation

enum TemplateLibrary {
    static let templates: [CompositionTemplate] = [
        CompositionTemplate(id: "thirds", name: "Rule of thirds", category: .minimal, description: "Place the subject on the third lines.", thumbnailStyle: "grid", isPro: false, elements: [
            item(.ruleOfThirds), item(.textHint, x: 0.08, y: 0.08, width: 0.84, height: 0.08, text: "align subject near an intersection")
        ]),
        CompositionTemplate(id: "center", name: "Center object", category: .product, description: "Clean centered object shot.", thumbnailStyle: "center", isPro: false, elements: [
            item(.centerCross, x: 0.5, y: 0.5, width: 0, height: 0), item(.circle, x: 0.32, y: 0.32, width: 0.36, height: 0.36, isDashed: true)
        ]),
        CompositionTemplate(id: "coffee", name: "Coffee top view", category: .coffee, description: "Top-down cafe shot.", thumbnailStyle: "coffee", isPro: false, elements: [
            item(.circle, x: 0.58, y: 0.20, width: 0.26, height: 0.26), item(.rectangle, x: 0.12, y: 0.56, width: 0.36, height: 0.24, isDashed: true), item(.diagonalLine, x: 0.02, y: 0.12, width: 0.96, height: 0.78)
        ]),
        CompositionTemplate(id: "mirror", name: "Mirror selfie", category: .selfie, description: "Clean vertical mirror selfie frame.", thumbnailStyle: "mirror", isPro: false, elements: [
            item(.rectangle, x: 0.24, y: 0.14, width: 0.52, height: 0.76, isDashed: true), item(.centerCross, x: 0.5, y: 0.42, width: 0, height: 0)
        ]),
        CompositionTemplate(id: "outfit", name: "Outfit full body", category: .outfit, description: "Full-body outfit frame.", thumbnailStyle: "outfit", isPro: false, elements: [
            item(.rectangle, x: 0.30, y: 0.08, width: 0.40, height: 0.84, isDashed: true), item(.line, x: 0.5, y: 0, width: 0, height: 1, opacity: 0.35)
        ]),
        CompositionTemplate(id: "travel", name: "Travel landscape thirds", category: .travel, description: "Horizon on thirds.", thumbnailStyle: "travel", isPro: false, elements: [
            item(.ruleOfThirds), item(.circle, x: 0.60, y: 0.50, width: 0.18, height: 0.18, isDashed: true)
        ]),
        CompositionTemplate(id: "food", name: "Food flat lay", category: .food, description: "Styled food layout.", thumbnailStyle: "food", isPro: false, elements: [
            item(.circle, x: 0.24, y: 0.28, width: 0.42, height: 0.42), item(.circle, x: 0.66, y: 0.16, width: 0.18, height: 0.18, isDashed: true)
        ]),
        CompositionTemplate(id: "space", name: "Negative space", category: .minimal, description: "One hero object with calm empty space.", thumbnailStyle: "minimal", isPro: false, elements: [
            item(.rectangle, x: 0.12, y: 0.62, width: 0.25, height: 0.18, isDashed: true), item(.textHint, x: 0.42, y: 0.22, width: 0.46, height: 0.10, text: "leave clean space")
        ])
    ]

    static let categories = TemplateCategory.allCases

    private static func item(_ type: OverlayElementType, x: CGFloat = 0, y: CGFloat = 0, width: CGFloat = 1, height: CGFloat = 1, opacity: Double = 0.72, lineWidth: CGFloat = 1.4, isDashed: Bool = false, text: String? = nil) -> OverlayElement {
        OverlayElement(type: type, x: x, y: y, width: width, height: height, opacity: opacity, lineWidth: lineWidth, isDashed: isDashed, text: text)
    }
}
