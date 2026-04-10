import SwiftUI

struct BottomFloatingTabBarStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .tint(AppColors.blush)
            .background(AppColors.background)
    }
}

extension View {
    func floatingTabBar() -> some View {
        modifier(BottomFloatingTabBarStyle())
    }
}
