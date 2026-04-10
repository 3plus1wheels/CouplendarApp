import SwiftUI

struct RootTabView: View {
    var body: some View {
        TabView {
            HomeView()
                .tabItem { Label("Home", systemImage: "house.fill") }
            CalendarView()
                .tabItem { Label("Calendar", systemImage: "calendar") }
            ExploreView()
                .tabItem { Label("Explore", systemImage: "safari") }
            ProfileView()
                .tabItem { Label("Profile", systemImage: "person.crop.circle") }
        }
        .floatingTabBar()
        .accessibilityIdentifier("root_tab_view")
    }
}

#Preview { RootTabView() }
