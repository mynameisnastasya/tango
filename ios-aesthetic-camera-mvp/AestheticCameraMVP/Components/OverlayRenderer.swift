import SwiftUI

struct OverlayRenderer: View {
    let template: CompositionTemplate
    var opacity: Double = 0.72
    var showHints: Bool = true

    var body: some View {
        Canvas { context, size in
            for element in template.elements {
                let rect = CGRect(x: size.width * element.x, y: size.height * element.y, width: size.width * element.width, height: size.height * element.height)
                let alpha = element.opacity * opacity
                var stroke = StrokeStyle(lineWidth: element.lineWidth, lineCap: .round, lineJoin: .round)
                if element.isDashed { stroke.dash = [8, 8] }
                let color = Color.white.opacity(alpha)
                switch element.type {
                case .line:
                    var path = Path()
                    path.move(to: CGPoint(x: rect.minX, y: rect.minY))
                    path.addLine(to: CGPoint(x: rect.minX + rect.width, y: rect.minY + rect.height))
                    context.stroke(path, with: .color(color), style: stroke)
                case .rectangle, .safeAreaBorder:
                    context.stroke(Path(roundedRect: rect, cornerRadius: 18), with: .color(color), style: stroke)
                case .circle:
                    context.stroke(Path(ellipseIn: rect), with: .color(color), style: stroke)
                case .diagonalLine:
                    var path = Path()
                    path.move(to: CGPoint(x: rect.minX, y: rect.maxY))
                    path.addLine(to: CGPoint(x: rect.maxX, y: rect.minY))
                    context.stroke(path, with: .color(color), style: stroke)
                case .centerCross:
                    var path = Path()
                    let length = min(size.width, size.height) * 0.08
                    path.move(to: CGPoint(x: rect.midX - length, y: rect.midY))
                    path.addLine(to: CGPoint(x: rect.midX + length, y: rect.midY))
                    path.move(to: CGPoint(x: rect.midX, y: rect.midY - length))
                    path.addLine(to: CGPoint(x: rect.midX, y: rect.midY + length))
                    context.stroke(path, with: .color(color), style: stroke)
                case .ruleOfThirds:
                    var path = Path()
                    for x in [size.width / 3, size.width * 2 / 3] { path.move(to: CGPoint(x: x, y: 0)); path.addLine(to: CGPoint(x: x, y: size.height)) }
                    for y in [size.height / 3, size.height * 2 / 3] { path.move(to: CGPoint(x: 0, y: y)); path.addLine(to: CGPoint(x: size.width, y: y)) }
                    context.stroke(path, with: .color(color), style: stroke)
                case .goldenSpiral:
                    context.stroke(Path(ellipseIn: rect), with: .color(color), style: stroke)
                case .textHint:
                    if showHints, let text = element.text {
                        let resolved = context.resolve(Text(text).font(.caption.bold()).foregroundStyle(.white))
                        context.draw(resolved, at: CGPoint(x: rect.midX, y: rect.midY))
                    }
                }
            }
        }
        .allowsHitTesting(false)
    }
}
