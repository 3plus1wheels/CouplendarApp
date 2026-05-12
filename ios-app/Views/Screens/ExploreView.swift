import SwiftUI
import UIKit

struct ExploreView: View {
    @EnvironmentObject private var authManager: AuthManager
    @Environment(\.openURL) private var openURL
    @StateObject private var viewModel = ExploreViewModel()
    @State private var showProfile = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: AppSpacing.lg) {
                    VStack(alignment: .leading, spacing: AppSpacing.xs) {
                        HStack {
                            Text("Explore")
                                .font(AppTypography.largeTitle)
                                .foregroundStyle(AppColors.primaryText)
                            Spacer()
                            headerCircleButton(
                                symbol: "person.fill",
                                action: { showProfile = true },
                                accessibilityIdentifier: "open_profile_button"
                            )
                        }

                        HStack(spacing: AppSpacing.xs) {
                            Image(systemName: "location.fill")
                                .font(.system(size: 12))
                                .foregroundStyle(AppColors.secondaryText)
                            Text(viewModel.locationText)
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.secondaryText)
                        }

                        if viewModel.isLocationDenied {
                            Button("Enable Location") {
                                if let url = URL(string: UIApplication.openSettingsURLString) {
                                    openURL(url)
                                }
                            }
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.blush)
                        }
                    }

                    if viewModel.isLoading {
                        ProgressView()
                            .frame(maxWidth: .infinity, alignment: .center)
                    } else if let error = viewModel.errorMessage {
                        Text(error)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.secondaryText)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    } else if viewModel.places.isEmpty {
                        Text("No places yet")
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.secondaryText)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    } else {
                        ForEach(viewModel.places) { place in
                            NavigationLink(value: place) {
                                PlaceCard(place: place)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
                .padding(AppSpacing.md)
            }
            .background(GlassBackgroundView())
            .task {
                viewModel.startLocation()
                await viewModel.load(authManager: authManager)
            }
            .navigationDestination(for: Place.self) { place in
                PlaceDetailView(place: place)
            }
            .sheet(isPresented: $showProfile) {
                NavigationStack {
                    ProfileView()
                }
                .environmentObject(authManager)
            }
        }
    }

    private func headerCircleButton(
        symbol: String,
        action: @escaping () -> Void,
        accessibilityIdentifier: String = ""
    ) -> some View {
        Button(action: action) {
            Image(systemName: symbol)
                .font(.system(size: 16, weight: .semibold))
                .foregroundStyle(AppColors.blush)
                .frame(width: 38, height: 38)
                .background(.white.opacity(0.85))
                .clipShape(Circle())
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier(accessibilityIdentifier.isEmpty ? "header_\(symbol)_button" : accessibilityIdentifier)
    }
}

#Preview { ExploreView() }
