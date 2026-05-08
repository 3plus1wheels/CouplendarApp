import SwiftUI

struct PlaceDetailView: View {
    @EnvironmentObject private var authManager: AuthManager
    let place: Place
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var detail: DiscoveryPlaceDetailDTO?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.lg) {
                RoundedRectangle(cornerRadius: 24, style: .continuous)
                    .fill(LinearGradient(colors: [AppColors.lavender.opacity(0.4), AppColors.blush.opacity(0.35)], startPoint: .topLeading, endPoint: .bottomTrailing))
                    .frame(height: 240)

                Text(place.name).font(AppTypography.largeTitle).foregroundStyle(AppColors.primaryText)
                HStack(spacing: AppSpacing.xs) {
                    ForEach(place.tags, id: \.self) { tag in
                        ChipView(title: tag, isActive: false, variant: .neutral)
                    }
                }

                Text(place.summary).font(AppTypography.body).foregroundStyle(AppColors.secondaryText)

                PrimaryCard {
                    HStack(spacing: AppSpacing.md) {
                        Label("Maps", systemImage: "map")
                        Label("Website", systemImage: "safari")
                        Label("Call", systemImage: "phone")
                    }
                    .font(AppTypography.caption)
                }

                if isLoading {
                    ProgressView()
                        .frame(maxWidth: .infinity, alignment: .center)
                } else if let errorMessage {
                    Text(errorMessage)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.secondaryText)
                } else if let detail {
                    reviewsCard(detail: detail)

                    if detail.videosAvailable {
                        videosCard(detail: detail)
                    }
                } else {
                    Text("No review details available")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.secondaryText)
                }
            }
            .padding(AppSpacing.md)
        }
        .background(GlassBackgroundView())
        .task {
            await loadDetail()
        }
    }

    @ViewBuilder
    private func reviewsCard(detail: DiscoveryPlaceDetailDTO) -> some View {
        PrimaryCard {
            VStack(alignment: .leading, spacing: AppSpacing.sm) {
                HStack(spacing: AppSpacing.xs) {
                    Image(systemName: "star.fill").foregroundStyle(AppColors.blush)
                    Text(detail.rating.map { String(format: "%.1f", $0) } ?? "—")
                        .font(AppTypography.cardTitle)
                    Text("(\(detail.reviewCount) reviews)")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.secondaryText)
                }

                if detail.topReviews.isEmpty {
                    Text("No reviews yet")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.secondaryText)
                } else {
                    ForEach(Array(detail.topReviews.enumerated()), id: \.offset) { _, review in
                        VStack(alignment: .leading, spacing: 4) {
                            Text(review.authorName)
                                .font(AppTypography.caption.weight(.semibold))
                            Text(review.text)
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.secondaryText)
                            if !review.relativeTimeDescription.isEmpty {
                                Text(review.relativeTimeDescription)
                                    .font(.caption2)
                                    .foregroundStyle(AppColors.secondaryText)
                            }
                        }
                    }
                }
            }
        }
    }

    @ViewBuilder
    private func videosCard(detail: DiscoveryPlaceDetailDTO) -> some View {
        PrimaryCard {
            VStack(alignment: .leading, spacing: AppSpacing.sm) {
                Text("TikTok Videos")
                    .font(AppTypography.cardTitle)
                ForEach(Array(detail.videos.enumerated()), id: \.offset) { _, video in
                    VStack(alignment: .leading, spacing: 2) {
                        Text(video.title)
                            .font(AppTypography.caption.weight(.semibold))
                        Text(video.url)
                            .font(.caption2)
                            .foregroundStyle(AppColors.secondaryText)
                    }
                }
            }
        }
    }

    private func loadDetail() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            detail = try await authManager.fetchDiscoveryPlaceDetail(id: place.discoveryId)
        } catch {
            detail = nil
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    PlaceDetailView(place: MockData.places[0])
        .environmentObject(AuthManager())
}
