import SwiftUI

struct SectionHeader: View {
    let title: String
    let subtitle: String?

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.xs) {
            Text(title).font(AppTypography.section).foregroundStyle(AppColors.primaryText)
            if let subtitle {
                Text(subtitle).font(AppTypography.caption).foregroundStyle(AppColors.secondaryText)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}
