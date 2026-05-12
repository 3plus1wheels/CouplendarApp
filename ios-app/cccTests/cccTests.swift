import Foundation
import Testing

@testable import CouplendarApp

struct cccTests {
    @MainActor
    @Test("HomeViewModel returns nearest future plan")
    func nextUpIsNearest() {
        let now = Date.now
        let plans = [
            Plan(id: UUID(), remoteId: 1, title: "Past", date: now.addingTimeInterval(-3_600), location: "", vibe: "Shared"),
            Plan(id: UUID(), remoteId: 2, title: "Later", date: now.addingTimeInterval(7_200), location: "", vibe: "Shared"),
            Plan(id: UUID(), remoteId: 3, title: "Soon", date: now.addingTimeInterval(1_800), location: "", vibe: "Shared")
        ]
        let vm = HomeViewModel(plans: plans)
        #expect(vm.nextUp?.title == "Soon")
    }

    @MainActor
    @Test("ExploreViewModel filters by selected tag")
    func exploreFilterByTag() {
        let vm = ExploreViewModel()
        vm.selectedTag = "Cafe"
        #expect(vm.filteredPlaces.allSatisfy { $0.category == "Cafe" })
    }

    @MainActor
    @Test("ExploreViewModel filters by search query")
    func exploreFilterByQuery() {
        let vm = ExploreViewModel()
        vm.query = "Rooftop"
        #expect(vm.filteredPlaces.count == 1)
        #expect(vm.filteredPlaces.first?.name == "Starlight Rooftop")
    }
}
