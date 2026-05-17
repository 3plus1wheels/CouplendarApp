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
                heroImage

                VStack(alignment: .leading, spacing: AppSpacing.sm) {
                    Text(place.name)
                        .font(AppTypography.largeTitle)
                        .foregroundStyle(AppColors.primaryText)

                    HStack(spacing: AppSpacing.xs) {
                        ForEach(place.tags, id: \.self) { tag in
                            ChipView(title: tag, isActive: false, variant: .neutral)
                        }
                    }

                    Text(place.summary)
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.secondaryText)
                }

                if let detail {
                    actionCard(detail: detail)
                }

                if isLoading {
                    ProgressView()
                        .frame(maxWidth: .infinity, alignment: .center)
                } else if let errorMessage {
                    Text(errorMessage)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.secondaryText)
                } else if let detail {
                    recommendationCard(detail: detail)
                    placeFactsCard(detail: detail)
                    videosCard(detail: detail)
                    photosCard(detail: detail)
                    reviewsCard(detail: detail)
                    hoursCard(detail: detail)
                } else {
                    Text("No place details available")
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
    private var heroImage: some View {
        AsyncImage(url: detailPhotoURLs.first ?? place.photoURL) { phase in
            switch phase {
            case .success(let image):
                image
                    .resizable()
                    .scaledToFill()
            case .failure, .empty:
                RoundedRectangle(cornerRadius: 24, style: .continuous)
                    .fill(LinearGradient(colors: [AppColors.lavender.opacity(0.4), AppColors.blush.opacity(0.35)], startPoint: .topLeading, endPoint: .bottomTrailing))
                    .overlay(
                        Image(systemName: "map")
                            .font(.system(size: 34, weight: .semibold))
                            .foregroundStyle(AppColors.primaryText.opacity(0.65))
                    )
            @unknown default:
                Color.clear
            }
        }
        .frame(height: 240)
        .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
    }

    @ViewBuilder
    private func actionCard(detail: DiscoveryPlaceDetailDTO) -> some View {
        PrimaryCard {
            HStack(spacing: AppSpacing.md) {
                actionLink(title: "Maps", systemImage: "map", urlString: detail.googleMapsURL.isEmpty ? detail.googleURI : detail.googleMapsURL)
                actionLink(title: "Website", systemImage: "safari", urlString: detail.websiteURL)
                actionLink(title: "Call", systemImage: "phone", urlString: phoneURLString(detail.phoneNumber))
            }
            .font(AppTypography.caption)
        }
    }

    @ViewBuilder
    private func recommendationCard(detail: DiscoveryPlaceDetailDTO) -> some View {
        PrimaryCard {
            VStack(alignment: .leading, spacing: AppSpacing.sm) {
                HStack {
                    Text("Why this place")
                        .font(AppTypography.cardTitle)
                    Spacer()
                    Text("\(Int(detail.suggestionScore.rounded()))% match")
                        .font(AppTypography.caption.weight(.semibold))
                        .foregroundStyle(AppColors.blush)
                }

                Text(detail.suggestionReason.isEmpty ? "Suggested from Google Maps place signals." : detail.suggestionReason)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.secondaryText)

                if !detail.suggestionBadges.isEmpty {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 96), spacing: 8)], alignment: .leading, spacing: 8) {
                        ForEach(detail.suggestionBadges, id: \.self) { badge in
                            Text(badge)
                                .font(.caption2.weight(.semibold))
                                .foregroundStyle(AppColors.primaryText)
                                .padding(.horizontal, 9)
                                .padding(.vertical, 5)
                                .background(AppColors.surface.opacity(0.7), in: Capsule())
                        }
                    }
                }

                let summary = bestSummary(detail)
                if !summary.isEmpty {
                    Text(summary)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.secondaryText)
                }
            }
        }
    }

    @ViewBuilder
    private func placeFactsCard(detail: DiscoveryPlaceDetailDTO) -> some View {
        PrimaryCard {
            VStack(alignment: .leading, spacing: AppSpacing.sm) {
                Text("Google Maps Signals")
                    .font(AppTypography.cardTitle)

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], alignment: .leading, spacing: AppSpacing.sm) {
                    factLabel(systemName: "star.fill", title: "Rating", value: ratingText(detail))
                    factLabel(systemName: "text.bubble.fill", title: "Reviews", value: "\(detail.reviewCount)")
                    factLabel(systemName: "clock.fill", title: "Status", value: openStatusText(detail.openNow))
                    factLabel(systemName: "tag.fill", title: "Price", value: formattedPriceLevel(detail.priceLevel))
                    factLabel(systemName: "mappin.and.ellipse", title: "Type", value: detail.primaryTypeDisplayName.isEmpty ? detail.category : detail.primaryTypeDisplayName)
                    factLabel(systemName: "checkmark.seal.fill", title: "Business", value: formattedBusinessStatus(detail.businessStatus))
                }

                if !enabledAmenities(detail).isEmpty {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 104), spacing: 8)], alignment: .leading, spacing: 8) {
                        ForEach(enabledAmenities(detail), id: \.self) { amenity in
                            Text(amenity)
                                .font(.caption2.weight(.semibold))
                                .foregroundStyle(AppColors.primaryText)
                                .padding(.horizontal, 9)
                                .padding(.vertical, 5)
                                .background(AppColors.surface.opacity(0.7), in: Capsule())
                        }
                    }
                }
            }
        }
    }

    @ViewBuilder
    private func videosCard(detail: DiscoveryPlaceDetailDTO) -> some View {
        if !detail.videos.isEmpty {
            PrimaryCard {
                VStack(alignment: .leading, spacing: AppSpacing.sm) {
                    Text("Videos")
                        .font(AppTypography.cardTitle)

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: AppSpacing.sm) {
                            ForEach(detail.videos) { video in
                                if let url = URL(string: video.sourceURL) {
                                    Link(destination: url) {
                                        videoTile(video)
                                    }
                                    .buttonStyle(.plain)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    private func videoTile(_ video: DiscoveryVideoDTO) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            AsyncImage(url: URL(string: video.thumbnailURL)) { phase in
                if let image = phase.image {
                    image
                        .resizable()
                        .scaledToFill()
                } else {
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .fill(AppColors.surface.opacity(0.55))
                        .overlay(
                            Image(systemName: "play.rectangle.fill")
                                .font(.system(size: 28, weight: .semibold))
                                .foregroundStyle(AppColors.blush)
                        )
                }
            }
            .frame(width: 170, height: 110)
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))

            Text(video.caption.isEmpty ? formattedVideoSource(video.source) : video.caption)
                .font(AppTypography.caption.weight(.semibold))
                .foregroundStyle(AppColors.primaryText)
                .lineLimit(2)

            if let viewsCount = video.viewsCount {
                Text("\(viewsCount.formatted()) views")
                    .font(.caption2)
                    .foregroundStyle(AppColors.secondaryText)
            }
        }
        .frame(width: 170, alignment: .leading)
    }

    @ViewBuilder
    private func photosCard(detail: DiscoveryPlaceDetailDTO) -> some View {
        if !detail.photoURLs.isEmpty {
            PrimaryCard {
                VStack(alignment: .leading, spacing: AppSpacing.sm) {
                    Text("Photos")
                        .font(AppTypography.cardTitle)

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: AppSpacing.sm) {
                            ForEach(detail.photoURLs, id: \.self) { urlString in
                                AsyncImage(url: URL(string: urlString)) { phase in
                                    if let image = phase.image {
                                        image
                                            .resizable()
                                            .scaledToFill()
                                    } else {
                                        RoundedRectangle(cornerRadius: 16, style: .continuous)
                                            .fill(AppColors.surface.opacity(0.5))
                                            .overlay(
                                                Image(systemName: "photo")
                                                    .foregroundStyle(AppColors.secondaryText)
                                            )
                                    }
                                }
                                .frame(width: 150, height: 110)
                                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                            }
                        }
                    }
                }
            }
        }
    }

    @ViewBuilder
    private func reviewsCard(detail: DiscoveryPlaceDetailDTO) -> some View {
        PrimaryCard {
            VStack(alignment: .leading, spacing: AppSpacing.sm) {
                HStack(spacing: AppSpacing.xs) {
                    Image(systemName: "star.fill")
                        .foregroundStyle(AppColors.blush)
                    Text(ratingText(detail))
                        .font(AppTypography.cardTitle)
                    Text("(\(detail.reviewCount) reviews)")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.secondaryText)
                }

                if !detail.reviewSummary.isEmpty {
                    Text(detail.reviewSummary)
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
    private func hoursCard(detail: DiscoveryPlaceDetailDTO) -> some View {
        if !detail.openingHours.isEmpty {
            PrimaryCard {
                VStack(alignment: .leading, spacing: AppSpacing.sm) {
                    Text("Hours")
                        .font(AppTypography.cardTitle)
                    ForEach(detail.openingHours, id: \.self) { line in
                        Text(line)
                            .font(AppTypography.caption)
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

    @ViewBuilder
    private func actionLink(title: String, systemImage: String, urlString: String) -> some View {
        if let url = URL(string: urlString), !urlString.isEmpty {
            Link(destination: url) {
                Label(title, systemImage: systemImage)
                    .frame(maxWidth: .infinity)
            }
        } else {
            Label(title, systemImage: systemImage)
                .frame(maxWidth: .infinity)
                .foregroundStyle(AppColors.secondaryText.opacity(0.55))
        }
    }

    @ViewBuilder
    private func factLabel(systemName: String, title: String, value: String) -> some View {
        HStack(alignment: .top, spacing: 8) {
            Image(systemName: systemName)
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(AppColors.blush)
                .frame(width: 18)
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.caption2)
                    .foregroundStyle(AppColors.secondaryText)
                Text(value.isEmpty ? "Not listed" : value)
                    .font(AppTypography.caption.weight(.semibold))
                    .foregroundStyle(AppColors.primaryText)
            }
        }
    }

    private var detailPhotoURLs: [URL] {
        guard let detail else { return [] }
        return detail.photoURLs.compactMap(URL.init(string:))
    }

    private func ratingText(_ detail: DiscoveryPlaceDetailDTO) -> String {
        detail.rating.map { String(format: "%.1f", $0) } ?? "-"
    }

    private func openStatusText(_ openNow: Bool?) -> String {
        switch openNow {
        case true: return "Open now"
        case false: return "Closed"
        case nil: return "Not listed"
        }
    }

    private func formattedPriceLevel(_ value: String) -> String {
        let cleaned = value
            .replacingOccurrences(of: "PRICE_LEVEL_", with: "")
            .replacingOccurrences(of: "_", with: " ")
            .capitalized
        return cleaned.isEmpty ? "Not listed" : cleaned
    }

    private func formattedBusinessStatus(_ value: String) -> String {
        let cleaned = value.replacingOccurrences(of: "_", with: " ").capitalized
        return cleaned.isEmpty ? "Not listed" : cleaned
    }

    private func bestSummary(_ detail: DiscoveryPlaceDetailDTO) -> String {
        if !detail.generativeSummary.isEmpty { return detail.generativeSummary }
        if !detail.editorialSummary.isEmpty { return detail.editorialSummary }
        return detail.reviewSummary
    }

    private func enabledAmenities(_ detail: DiscoveryPlaceDetailDTO) -> [String] {
        detail.amenities
            .filter { $0.value }
            .map { formattedAmenity($0.key) }
            .sorted()
    }

    private func formattedAmenity(_ key: String) -> String {
        key.reduce(into: "") { result, character in
            if character.isUppercase {
                result.append(" ")
            }
            result.append(character)
        }
        .capitalized
    }

    private func phoneURLString(_ phoneNumber: String) -> String {
        let digits = phoneNumber.filter { $0.isNumber || $0 == "+" }
        return digits.isEmpty ? "" : "tel://\(digits)"
    }

    private func formattedVideoSource(_ source: String) -> String {
        source.replacingOccurrences(of: "_", with: " ").capitalized
    }
}

#Preview {
    PlaceDetailView(place: MockData.places[0])
        .environmentObject(AuthManager())
}
