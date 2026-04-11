import Foundation

struct Plan: Identifiable, Hashable {
    let id: UUID
    let title: String
    let date: Date
    let location: String
    let vibe: String
}
