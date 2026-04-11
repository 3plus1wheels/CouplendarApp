import SwiftUI

struct GlassCardStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(AppSpacing.md)
            .background(
                LinearGradient(
                    colors: [AppColors.glass, AppColors.surface],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
            .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
            .shadow(color: AppColors.primaryText.opacity(AppShadows.opacity), radius: AppShadows.radius, x: 0, y: AppShadows.y)
    }
}

extension View {
    func glassCard() -> some View {
        modifier(GlassCardStyle())
    }
}
