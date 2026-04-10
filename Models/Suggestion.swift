import Foundation

struct Suggestion: Identifiable, Hashable {
    let id: UUID
    let title: String
    let subtitle: String
    let emoji: String
}
