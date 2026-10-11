import Foundation
import CoreGraphics

enum OverlayElementType: String, Codable, CaseIterable, Identifiable {
    case line
    case rectangle
    case circle
    case diagonalLine
    case centerCross
    case textHint
    case safeAreaBorder
    case ruleOfThirds
    case goldenSpiral
    var id: String { rawValue }
}
