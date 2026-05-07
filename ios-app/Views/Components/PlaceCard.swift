import SwiftUI

struct PlaceCard: View {
    let place: Place

    private var detailText: String {
        place.summary.isEmpty ? place.category : place.summary
    }

    private var ratingText: String {
        guard let rating = place.rating else {
            return "—"
        }
        return String(format: "%.1f", rating)
    }

    var body: some View {
        HStack(alignment: .top, spacing: AppSpacing.md) {
            AsyncImage(url: place.photoURL) { phase in
                if let image = phase.image {
                    image
                        .resizable()
                        .scaledToFill()
                } else {
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .fill(AppColors.surface.opacity(0.4))
                        .overlay(
                            Image(systemName: "photo")
                                .font(.system(size: 18))
                                .foregroundStyle(AppColors.secondaryText)
                        )
                }
            }
            .frame(width: 86, height: 86)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))

            VStack(alignment: .leading, spacing: AppSpacing.xs) {
                Text(place.name)
                    .font(AppTypography.cardTitle)
                    .foregroundStyle(AppColors.primaryText)

                HStack(spacing: AppSpacing.xs) {
                    Image(systemName: "star.fill")
                        .font(.system(size: 12))
                        .foregroundStyle(AppColors.blush)
                    Text(ratingText)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.secondaryText)
                    Text("•")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.secondaryText)
                    Text(place.distance)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.secondaryText)
                }

                Text(detailText)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.secondaryText)
            }

            Spacer(minLength: 0)
        }
        .glassCard()
    }
}
