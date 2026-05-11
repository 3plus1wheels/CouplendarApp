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
                    } else if !detail.videoRefreshError.isEmpty {
                        videoErrorCard(detail: detail)
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
                Text("Relevant YouTube Shorts")
                    .font(AppTypography.cardTitle)

                if let updatedText = formattedVideosUpdatedAt(detail.videosLastUpdated) {
                    Text("Updated \(updatedText)")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.secondaryText)
                }

                ForEach(Array(detail.videos.prefix(3).enumerated()), id: \.offset) { _, video in
                    shortCard(video: video)
                }
            }
        }
    }

    @ViewBuilder
    private func shortCard(video: DiscoveryVideoDTO) -> some View {
        if let url = URL(string: video.sourceURL) {
            Link(destination: url) {
                VStack(alignment: .leading, spacing: AppSpacing.sm) {
                    ZStack(alignment: .topLeading) {
                        RoundedRectangle(cornerRadius: 18, style: .continuous)
                            .fill(AppColors.secondaryText.opacity(0.08))

                        AsyncImage(url: URL(string: video.thumbnailURL)) { phase in
                            switch phase {
                            case .success(let image):
                                image
                                    .resizable()
                                    .scaledToFill()
                            case .failure, .empty:
                                RoundedRectangle(cornerRadius: 18, style: .continuous)
                                    .fill(LinearGradient(colors: [AppColors.lavender.opacity(0.35), AppColors.blush.opacity(0.25)], startPoint: .topLeading, endPoint: .bottomTrailing))
                                    .overlay(
                                        Image(systemName: "play.rectangle.fill")
                                            .font(.system(size: 36))
                                            .foregroundStyle(AppColors.primaryText.opacity(0.7))
                                    )
                            @unknown default:
                                Color.clear
                            }
                        }
                        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))

                        Text("Short")
                            .font(AppTypography.caption.weight(.semibold))
                            .foregroundStyle(AppColors.primaryText)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .background(.ultraThinMaterial, in: Capsule())
                            .padding(12)
                    }
                    .frame(maxWidth: .infinity)
                    .frame(height: 280)
                    .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))

                    VStack(alignment: .leading, spacing: 6) {
                        Text(video.title)
                            .font(AppTypography.caption.weight(.semibold))
                            .foregroundStyle(AppColors.primaryText)
                            .multilineTextAlignment(.leading)

                        if !displayChannelName(for: video).isEmpty {
                            Text(displayChannelName(for: video))
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.secondaryText)
                                .multilineTextAlignment(.leading)
                        }

                        HStack(spacing: AppSpacing.md) {
                            statLabel(systemName: "eye.fill", value: compactCount(video.viewsCount))
                            statLabel(systemName: "heart.fill", value: compactCount(video.likesCount))
                        }
                    }
                }
            }
            .buttonStyle(.plain)
        }
    }

    @ViewBuilder
    private func videoErrorCard(detail: DiscoveryPlaceDetailDTO) -> some View {
        PrimaryCard {
            VStack(alignment: .leading, spacing: AppSpacing.sm) {
                Text("Video Refresh Error")
                    .font(AppTypography.cardTitle)
                Text(detail.videoRefreshError)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.secondaryText)
                    .textSelection(.enabled)
            }
        }
    }

    private func loadDetail() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            detail = try await authManager.fetchDiscoveryPlaceDetail(id: place.discoveryId)
            Task {
                _ = try? await authManager.refreshDiscoveryPlaceVideos(id: place.discoveryId)
            }
        } catch {
            detail = nil
            errorMessage = error.localizedDescription
        }
    }

    @ViewBuilder
    private func statLabel(systemName: String, value: String) -> some View {
        HStack(spacing: 6) {
            Image(systemName: systemName)
            Text(value)
        }
        .font(AppTypography.caption)
        .foregroundStyle(AppColors.secondaryText)
    }

    private func compactCount(_ value: Int?) -> String {
        guard let value else { return "—" }
        if value >= 1_000_000 {
            return String(format: "%.1fM", Double(value) / 1_000_000).replacingOccurrences(of: ".0", with: "")
        }
        if value >= 1_000 {
            return String(format: "%.1fK", Double(value) / 1_000).replacingOccurrences(of: ".0", with: "")
        }
        return "\(value)"
    }

    private func displayChannelName(for video: DiscoveryVideoDTO) -> String {
        if !video.creatorDisplayName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return video.creatorDisplayName
        }
        return video.creatorUsername.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func formattedVideosUpdatedAt(_ value: String?) -> String? {
        guard let value, let date = Self.parseISO8601(value) else { return nil }
        return relativeDateFormatter.localizedString(for: date, relativeTo: Date())
    }

    private static func parseISO8601(_ value: String) -> Date? {
        if let date = iso8601FractionalFormatter.date(from: value) {
            return date
        }
        return iso8601Formatter.date(from: value)
    }

    private static let iso8601FractionalFormatter: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter
    }()

    private static let iso8601Formatter: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        return formatter
    }()

    private let relativeDateFormatter: RelativeDateTimeFormatter = {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .full
        return formatter
    }()
}

#Preview {
    PlaceDetailView(place: MockData.places[0])
        .environmentObject(AuthManager())
}
