import SwiftUI

struct ChipView: View {
    enum Variant { case blush, lavender, mint, neutral }

    let title: String
    let isActive: Bool
    let variant: Variant

    private var tint: Color {
        switch variant {
        case .blush: AppColors.blush
        case .lavender: AppColors.lavender
        case .mint: AppColors.mint
        case .neutral: AppColors.neutralChip
        }
    }

    var body: some View {
        Text(title)
            .font(AppTypography.caption.weight(.medium))
            .foregroundStyle(isActive ? Color.white : AppColors.primaryText)
            .padding(.horizontal, AppSpacing.md)
            .padding(.vertical, AppSpacing.xs)
            .background(isActive ? tint : tint.opacity(0.28))
            .clipShape(Capsule())
    }
}
