import Foundation

enum MockData {
    static let plans: [Plan] = [
        Plan(id: UUID(), remoteId: nil, title: "Sunset Picnic", date: .now.addingTimeInterval(86_400), location: "River Valley", vibe: "Romantic"),
        Plan(id: UUID(), remoteId: nil, title: "Coffee Date", date: .now.addingTimeInterval(172_800), location: "Honey Bean", vibe: "Cozy"),
        Plan(id: UUID(), remoteId: nil, title: "Dance Class", date: .now.addingTimeInterval(345_600), location: "Luna Studio", vibe: "Playful")
    ]

    static let suggestions: [Suggestion] = [
        Suggestion(id: UUID(), title: "Try a Surprise Note", subtitle: "Leave one in their bag before work", emoji: "💌"),
        Suggestion(id: UUID(), title: "30-Minute Walk", subtitle: "No phones, just catch up", emoji: "🌿")
    ]

    static let reminders: [String] = [
        "Partner pulse: Alex has a stressful week. Keep plans light.",
        "Anniversary month starts soon. Reserve dinner this week."
    ]

    static let places: [Place] = [
        Place(id: UUID(), discoveryId: 1, name: "Bloom Garden Cafe", category: "Cafe", tags: ["Open now", "Brunch"], distance: "1.2 km", summary: "Recommended for 4.6 stars, 102 Google reviews, open now, cafe.", suggestionScore: 91, suggestionBadges: ["Highly rated", "Open now", "Brunch"], rating: 4.6, reviewCount: 102, photoURL: nil),
        Place(id: UUID(), discoveryId: 2, name: "Starlight Rooftop", category: "Dinner", tags: ["Popular", "Cocktails"], distance: "3.8 km", summary: "Recommended for skyline views and strong Google review signals.", suggestionScore: 87, suggestionBadges: ["Popular", "Cocktails"], rating: 4.4, reviewCount: 88, photoURL: nil),
        Place(id: UUID(), discoveryId: 3, name: "Mint Pottery Studio", category: "Activity", tags: ["Highly rated", "Creative"], distance: "2.4 km", summary: "Recommended for 4.7 stars and hands-on date energy.", suggestionScore: 89, suggestionBadges: ["Highly rated", "Reservations"], rating: 4.7, reviewCount: 46, photoURL: nil)
    ]

    static let profile = UserProfile(
        yourName: "Vova",
        partnerName: "Alex",
        relationshipLabel: "Planning life one date at a time",
        anniversaryText: "2 years together",
        notificationsEnabled: true
    )
}
