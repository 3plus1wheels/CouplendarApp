# Couplendar Implementation Status

This document tracks what is currently implemented in the SwiftUI app and what is still stubbed or unfinished, screen by screen.

## App Shell

### Implemented
- Native `@main` app entry point in `App/CouplendarApp.swift`
- Root `TabView` shell in `App/RootTabView.swift`
- Four bottom tabs:
  - Home
  - Calendar
  - Explore
  - Profile
- Shared background and tab styling

### Not Implemented
- Custom tab bar animations
- Deep-link routing
- State restoration across app launches

## Home Screen

### Implemented
- Greeting header
- `Next up` hero card
- Horizontal upcoming plans rail
- Suggestions section
- Partner pulse / reminder section
- Shared card, chip, and section header components

### Not Implemented
- Real scheduling logic
- Event creation flow
- Editing or deleting plans
- Remote or persistent data source

## Calendar Screen

### Implemented
- Month title header
- Segmented `Day / Week / Month` picker
- Mock schedule list
- Floating add button
- Native SwiftUI scrolling layout

### Not Implemented
- Real calendar grid
- Day/week/month view switching logic
- Time-block drag and drop
- Event creation from the floating action button

## Explore Screen

### Implemented
- Search field
- Horizontal filter chips
- Trending section
- Vertically scrolling place cards
- Navigation to place detail

### Not Implemented
- Network-backed search
- Saved places collection
- Sorting or ranking logic beyond simple local filtering
- Image loading from remote sources

## Place Detail Screen

### Implemented
- Hero image placeholder area
- Place title and tags
- Short summary text
- Utility action row
- `Why it fits you two` section

### Not Implemented
- Real map integration
- Website, call, and menu actions
- Reviews or social proof data
- Saved state or bookmarking persistence

## Profile Screen

### Implemented
- Profile header
- Paired avatar presentation
- Edit / Save toggle UI
- Reminder toggle
- Preferences cards

### Not Implemented
- Real editing workflow
- Persistence for profile settings
- Notification permissions flow
- Account sync or authentication

## Design System

### Implemented
- Shared colors
- Typography scale
- Spacing tokens
- Shadow tokens
- Glass card styling
- Reusable card, chip, section header, avatar, and place card components

### Not Implemented
- Full theme switching
- Dark mode-specific design polish
- Brand icon set or custom illustrations

## Data and Models

### Implemented
- Local mock data for plans, suggestions, places, and profile
- Lightweight view models for each screen
- Native SwiftUI state management with `@State` and `@StateObject`

### Not Implemented
- SwiftData or Core Data persistence
- Backend API layer
- Sync, caching, or offline conflict handling

## Testing

### Implemented
- Unit tests for:
  - Home `nextUp` selection
  - Explore tag filtering
  - Explore query filtering
- UI smoke test for the root tab bar

### Not Implemented
- Snapshot tests
- Screen-by-screen visual regression tests
- Full UI test coverage for each tab and detail view

## Build Status

### Implemented
- The app target builds successfully in Xcode

### Not Implemented
- Full automated test run completion has not been confirmed yet in this environment

## Summary

The app is now a native SwiftUI prototype with the requested 4-tab structure, mock data, reusable design system, and core screens in place. The remaining work is mainly product depth: persistence, richer navigation, real interactions, and more complete calendar behavior.
