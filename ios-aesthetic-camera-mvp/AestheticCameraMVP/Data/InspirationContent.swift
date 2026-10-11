import Foundation

struct InspirationArticle: Identifiable, Hashable {
    let id = UUID()
    let title: String
    let tips: [String]
}

enum InspirationContent {
    static let articles = [
        InspirationArticle(title: "How to shoot coffee aesthetically", tips: ["Use window light", "Keep one hero cup", "Leave calm negative space"]),
        InspirationArticle(title: "How to use negative space", tips: ["Do not fill every corner", "Let the object breathe", "Keep the background clean"]),
        InspirationArticle(title: "How to shoot outfit photos", tips: ["Step back", "Keep shoes inside frame", "Use clean vertical lines"])
    ]
}
