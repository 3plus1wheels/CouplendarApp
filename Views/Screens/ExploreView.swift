import SwiftUI

struct ExploreView: View {
    @StateObject private var viewModel = ExploreViewModel()

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: AppSpacing.lg) {
                    Text("Explore").font(AppTypography.largeTitle).foregroundStyle(AppColors.primaryText)

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
        }
    }
}

#Preview { ExploreView() }
