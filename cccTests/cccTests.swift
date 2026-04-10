import Foundation
import Testing

@testable import CouplendarApp

struct cccTests {
    @MainActor
    @Test("HomeViewModel returns nearest next plan")
    func nextUpIsNearest() {
        let vm = HomeViewModel()
        let sorted = vm.plans.sorted { $0.date < $1.date }
        #expect(vm.nextUp == sorted.first)
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
