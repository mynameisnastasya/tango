import Foundation

enum TemplateCategory: String, CaseIterable, Identifiable, Codable {
    case coffee = "Coffee"
    case food = "Food"
    case travel = "Travel"
    case outfit = "Outfit"
    case selfie = "Selfie"
    case interior = "Interior"
    case product = "Product"
    case minimal = "Minimal"
    case street = "Street"
    case flatLay = "Flat lay"
    var id: String { rawValue }
}

struct CompositionTemplate: Identifiable, Codable, Hashable {
    let id: String
    let name: String
    let category: TemplateCategory
    let description: String
    let thumbnailStyle: String
    let isPro: Bool
    let elements: [OverlayElement]
}
