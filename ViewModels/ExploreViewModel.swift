import Foundation
import Combine

@MainActor
final class ExploreViewModel: ObservableObject {
    @Published var query: String = ""
    @Published var selectedTag: String = "All"
    @Published var places: [Place] = MockData.places

    let tags: [String] = ["All", "Cafe", "Dinner", "Activity"]

    var filteredPlaces: [Place] {
        places.filter { place in
            let tagMatch = selectedTag == "All" || place.category == selectedTag
            let queryMatch = query.isEmpty || place.name.localizedCaseInsensitiveContains(query)
            return tagMatch && queryMatch
        }
    }
}
