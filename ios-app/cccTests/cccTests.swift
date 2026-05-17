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
    @Test("ExploreViewModel tracks active search text")
    func exploreSearchState() {
        let vm = ExploreViewModel()
        vm.searchText = "Rooftop"
        #expect(vm.hasActiveSearch)
        vm.clearSearch()
        #expect(!vm.hasActiveSearch)
    }

    @Test("Discovery endpoint adds query item")
    func discoveryEndpointQueryItem() {
        #expect(Endpoint.discoveryTrending(query: "coffee").queryItems.first?.name == "q")
        #expect(Endpoint.discoveryTrending(query: "coffee").queryItems.first?.value == "coffee")
        #expect(Endpoint.discoveryTrending(query: "   ").queryItems.isEmpty)
    }
}
