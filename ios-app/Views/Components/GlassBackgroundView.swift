import SwiftUI

struct GlassBackgroundView: View {
    var body: some View {
        LinearGradient(
            colors: [AppColors.background, AppColors.lavender.opacity(0.15), AppColors.blush.opacity(0.15)],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
        .ignoresSafeArea()
    }
}
