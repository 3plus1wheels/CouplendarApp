import SwiftUI

struct PlaceCard: View {
    let place: Place

    private var detailText: String {
        place.summary.isEmpty ? place.category : place.summary
    }

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            Text(place.name)
                .font(AppTypography.cardTitle)
                .foregroundStyle(AppColors.primaryText)

            Text(detailText)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.secondaryText)
        }
        .glassCard()
    }
}
