import Foundation

struct Place: Identifiable, Hashable {
    let id: UUID
    let name: String
    let category: String
    let tags: [String]
    let distance: String
    let summary: String
}
