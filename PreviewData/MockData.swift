import Foundation

enum MockData {
    static let plans: [Plan] = [
        Plan(id: UUID(), title: "Sunset Picnic", date: .now.addingTimeInterval(86_400), location: "River Valley", vibe: "Romantic"),
        Plan(id: UUID(), title: "Coffee Date", date: .now.addingTimeInterval(172_800), location: "Honey Bean", vibe: "Cozy"),
        Plan(id: UUID(), title: "Dance Class", date: .now.addingTimeInterval(345_600), location: "Luna Studio", vibe: "Playful")
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
        Place(id: UUID(), name: "Bloom Garden Cafe", category: "Cafe", tags: ["Calm", "Brunch"], distance: "1.2 km", summary: "Floral brunch spot with cozy corners and soft jazz."),
        Place(id: UUID(), name: "Starlight Rooftop", category: "Dinner", tags: ["Views", "Date Night"], distance: "3.8 km", summary: "Modern rooftop dining with skyline views."),
        Place(id: UUID(), name: "Mint Pottery Studio", category: "Activity", tags: ["Hands-on", "Creative"], distance: "2.4 km", summary: "Wheel-throwing class perfect for a playful date.")
    ]

    static let profile = UserProfile(
        yourName: "Vova",
        partnerName: "Alex",
        relationshipLabel: "Planning life one date at a time",
        anniversaryText: "2 years together",
        notificationsEnabled: true
    )
}
