import SwiftUI

struct ExploreView: View {
    @EnvironmentObject private var authManager: AuthManager
    @StateObject private var viewModel = ExploreViewModel()
    @State private var showProfile = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: AppSpacing.lg) {
                    HStack {
                        Text("Explore").font(AppTypography.largeTitle).foregroundStyle(AppColors.primaryText)
                        Spacer()
                        Button {
                            showProfile = true
                        } label: {
                            Image(systemName: "person.crop.circle.fill")
                                .font(.system(size: 30))
                                .foregroundStyle(AppColors.blush)
                        }
                        .buttonStyle(.plain)
                        .accessibilityIdentifier("open_profile_button")
                    }

                    TextField("Search places", text: $viewModel.query)
                        .textFieldStyle(.roundedBorder)

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: AppSpacing.xs) {
                            ForEach(viewModel.tags, id: \.self) { tag in
                                Button {
                                    viewModel.selectedTag = tag
                                } label: {
                                    ChipView(
                                        title: tag,
                                        isActive: viewModel.selectedTag == tag,
                                        variant: tag == "Dinner" ? .lavender : (tag == "Activity" ? .mint : .blush)
                                    )
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }

                    SectionHeader(title: "Trending", subtitle: "Picked for your shared vibe")

                    ForEach(viewModel.filteredPlaces) { place in
                        NavigationLink(value: place) {
                            PlaceCard(place: place)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(AppSpacing.md)
            }
            .background(GlassBackgroundView())
            .navigationDestination(for: Place.self) { place in
                PlaceDetailView(place: place)
            }
            .sheet(isPresented: $showProfile) {
                NavigationStack {
                    ProfileView()
                }
                .environmentObject(authManager)
            }
        }
    }
}

#Preview { ExploreView() }
