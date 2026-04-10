import SwiftUI

struct PlaceCard: View {
    let place: Place

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .fill(LinearGradient(colors: [AppColors.lavender.opacity(0.35), AppColors.mint.opacity(0.25)], startPoint: .topLeading, endPoint: .bottomTrailing))
                .frame(height: 140)
                .overlay(alignment: .topTrailing) {
                    Image(systemName: "bookmark")
                        .padding(10)
                        .background(.ultraThinMaterial)
                        .clipShape(Circle())
                        .padding(10)
                }

            Text(place.name).font(AppTypography.cardTitle).foregroundStyle(AppColors.primaryText)

            HStack(spacing: AppSpacing.xs) {
                ForEach(place.tags, id: \.self) { tag in
                    ChipView(title: tag, isActive: false, variant: .neutral)
                }
            }

            Text("\(place.category) • \(place.distance)")
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.secondaryText)
        }
        .glassCard()
    }
}
