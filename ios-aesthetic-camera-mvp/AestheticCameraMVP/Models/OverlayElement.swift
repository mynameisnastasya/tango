import Foundation
import CoreGraphics

struct OverlayElement: Identifiable, Codable, Hashable {
    var id = UUID()
    let type: OverlayElementType
    let x: CGFloat
    let y: CGFloat
    let width: CGFloat
    let height: CGFloat
    let opacity: Double
    let lineWidth: CGFloat
    let isDashed: Bool
    let text: String?
}
