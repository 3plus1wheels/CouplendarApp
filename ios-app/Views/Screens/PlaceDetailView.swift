import SwiftUI

struct PlaceDetailView: View {
    let place: Place

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

                PrimaryCard {
                    VStack(alignment: .leading, spacing: AppSpacing.xs) {
                        Text("Why it fits you two").font(AppTypography.cardTitle)
                        Text("Low-noise vibe, warm lighting, and enough space for long conversation.")
                            .font(AppTypography.body)
                            .foregroundStyle(AppColors.secondaryText)
                    }
                }
            }
            .padding(AppSpacing.md)
        }
        .background(GlassBackgroundView())
    }
}

#Preview { PlaceDetailView(place: MockData.places[0]) }
