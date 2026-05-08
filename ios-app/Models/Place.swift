import Foundation

struct Place: Identifiable, Hashable {
    let id: UUID
    let discoveryId: Int
    let name: String
    let category: String
    let tags: [String]
    let distance: String
    let summary: String
    let rating: Double?
    let reviewCount: Int
    let photoURL: URL?
}
