import SwiftUI
import UIKit

struct BottomFloatingTabBarStyle: ViewModifier {
    init() {
        let appearance = UITabBarAppearance()
        appearance.configureWithOpaqueBackground()
        appearance.backgroundColor = UIColor(AppColors.background).withAlphaComponent(0.94)
        appearance.shadowColor = .clear

        let normalIconColor = UIColor(AppColors.secondaryText)
        let selectedIconColor = UIColor(AppColors.blush)
        let normalTextColor = UIColor(AppColors.primaryText).withAlphaComponent(0.88)
        let selectedTextColor = UIColor(AppColors.blush)

        [appearance.stackedLayoutAppearance, appearance.inlineLayoutAppearance, appearance.compactInlineLayoutAppearance].forEach { itemAppearance in
            itemAppearance.normal.iconColor = normalIconColor
            itemAppearance.normal.titleTextAttributes = [.foregroundColor: normalTextColor]
            itemAppearance.selected.iconColor = selectedIconColor
            itemAppearance.selected.titleTextAttributes = [.foregroundColor: selectedTextColor]
        }

        UITabBar.appearance().standardAppearance = appearance
        UITabBar.appearance().scrollEdgeAppearance = appearance
        UITabBar.appearance().selectionIndicatorImage = UIImage()
        UITabBar.appearance().backgroundImage = UIImage()
        UITabBar.appearance().shadowImage = UIImage()
        UITabBar.appearance().isTranslucent = true
    }

    func body(content: Content) -> some View {
        content
            .tint(AppColors.blush)
            .toolbarBackground(.visible, for: .tabBar)
            .toolbarBackground(AppColors.background.opacity(0.94), for: .tabBar)
            .background(AppColors.background)
    }
}

extension View {
    func floatingTabBar() -> some View {
        modifier(BottomFloatingTabBarStyle())
    }
}
