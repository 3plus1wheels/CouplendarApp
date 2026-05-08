import Foundation

struct Plan: Identifiable, Hashable {
    let id: UUID
    let remoteId: Int?
    let title: String
    let date: Date
    let location: String
    let vibe: String
}
