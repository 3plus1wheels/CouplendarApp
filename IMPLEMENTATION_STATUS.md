# Couplendar Implementation Status

This document reflects the current auth-first split of the project:
- `ios-app/` contains the SwiftUI frontend
- `backend/` contains the Django + DRF + JWT backend

The app still contains the earlier mock-data tab screens, but the new work centers on authentication and profile sync first.

## Project Split

### Implemented
- Frontend moved into [`/Users/vova_nguyen/Documents/ccc/ios-app`](/Users/vova_nguyen/Documents/ccc/ios-app)
- Backend scaffold created in [`/Users/vova_nguyen/Documents/ccc/backend`](/Users/vova_nguyen/Documents/ccc/backend)
- Frontend and backend are separated cleanly enough to evolve independently

### Not Implemented
- Production deployment wiring between the two projects
- Shared monorepo tooling for release/versioning
- CI pipeline covering both stacks together

## App Shell

### Implemented
- Native `@main` app entry point in [`/Users/vova_nguyen/Documents/ccc/ios-app/App/CouplendarApp.swift`](/Users/vova_nguyen/Documents/ccc/ios-app/App/CouplendarApp.swift)
- Auth-gated root flow through [`/Users/vova_nguyen/Documents/ccc/ios-app/Views/Screens/Auth/AuthGateView.swift`](/Users/vova_nguyen/Documents/ccc/ios-app/Views/Screens/Auth/AuthGateView.swift)
- Session restore on launch through `AuthManager.restoreSession()`
- Post-login shell still routes into the existing tab container in [`/Users/vova_nguyen/Documents/ccc/ios-app/App/RootTabView.swift`](/Users/vova_nguyen/Documents/ccc/ios-app/App/RootTabView.swift)

### Not Implemented
- A full navigation rewrite after auth
- Deep-link routing
- State restoration beyond token-based session restore

## Authentication Flow

### Implemented
- Login screen in [`/Users/vova_nguyen/Documents/ccc/ios-app/Views/Screens/Auth/LoginView.swift`](/Users/vova_nguyen/Documents/ccc/ios-app/Views/Screens/Auth/LoginView.swift)
- Register screen in [`/Users/vova_nguyen/Documents/ccc/ios-app/Views/Screens/Auth/RegisterView.swift`](/Users/vova_nguyen/Documents/ccc/ios-app/Views/Screens/Auth/RegisterView.swift)
- JWT token storage in [`/Users/vova_nguyen/Documents/ccc/ios-app/Core/Auth/TokenStore.swift`](/Users/vova_nguyen/Documents/ccc/ios-app/Core/Auth/TokenStore.swift)
- Auth state management in [`/Users/vova_nguyen/Documents/ccc/ios-app/Core/Auth/AuthManager.swift`](/Users/vova_nguyen/Documents/ccc/ios-app/Core/Auth/AuthManager.swift)
- API client in [`/Users/vova_nguyen/Documents/ccc/ios-app/Core/Networking/APIClient.swift`](/Users/vova_nguyen/Documents/ccc/ios-app/Core/Networking/APIClient.swift)
- Auth response and user models in [`/Users/vova_nguyen/Documents/ccc/ios-app/Models/AuthResponse.swift`](/Users/vova_nguyen/Documents/ccc/ios-app/Models/AuthResponse.swift) and [`/Users/vova_nguyen/Documents/ccc/ios-app/Models/User.swift`](/Users/vova_nguyen/Documents/ccc/ios-app/Models/User.swift)
- Login, register, me, and profile wiring on the Swift side

### Not Implemented
- Forgot password flow
- Email verification flow
- Social login
- Token refresh retries inside the client layer
- Account deletion

## Profile Screen

### Implemented
- Current-user display from backend profile data
- Profile fetch on appear / task
- Profile patch flow for display name, first name, last name, and city
- Logout action that clears local auth state

### Not Implemented
- Avatar upload
- Notification settings persistence
- Validation feedback beyond basic request failure handling
- Profile photo editing

## Home Screen

### Implemented
- Legacy SwiftUI home tab still exists in [`/Users/vova_nguyen/Documents/ccc/ios-app/Views/Screens/HomeView.swift`](/Users/vova_nguyen/Documents/ccc/ios-app/Views/Screens/HomeView.swift)
- Mock-data-driven greeting, next-up card, upcoming list, suggestions, and reminders sections
- Shared card and section components reused across the screen

### Not Implemented
- Backend-backed home feed
- Event creation or editing flows
- Real scheduling logic
- Empty-state behavior driven by live data

## Calendar Screen

### Implemented
- Legacy mock calendar tab remains in [`/Users/vova_nguyen/Documents/ccc/ios-app/Views/Screens/CalendarView.swift`](/Users/vova_nguyen/Documents/ccc/ios-app/Views/Screens/CalendarView.swift)
- Month heading, segmented mode picker, and mock event list
- Floating add button shell

### Not Implemented
- Real calendar grid
- Day/week/month switching logic
- Event drag-and-drop or time-block editing
- Create-event flow from the add button

## Explore Screen

### Implemented
- Legacy explore screen still exists in [`/Users/vova_nguyen/Documents/ccc/ios-app/Views/Screens/ExploreView.swift`](/Users/vova_nguyen/Documents/ccc/ios-app/Views/Screens/ExploreView.swift)
- Local search and filtering behavior
- Simple place card browsing and navigation shell

### Not Implemented
- Network-backed search
- Saved places
- Ranking/sorting beyond local filtering
- Remote image loading

## Place Detail Screen

### Implemented
- Legacy place detail screen still exists in [`/Users/vova_nguyen/Documents/ccc/ios-app/Views/Screens/PlaceDetailView.swift`](/Users/vova_nguyen/Documents/ccc/ios-app/Views/Screens/PlaceDetailView.swift)
- Basic hero, title, summary, and related content layout

### Not Implemented
- Maps integration
- Live website / call / menu actions
- Reviews or social proof
- Saved/bookmarked state persistence

## Design System

### Implemented
- Shared colors, spacing, typography, and shadows in `DesignSystem/`
- Reusable SwiftUI building blocks such as cards, chips, section headers, and avatar stacks
- Theming is centralized enough to support the current UI

### Not Implemented
- Full theme switching
- Dark-mode-specific visual polish
- Brand illustration system

## Backend

### Implemented
- Django project scaffold in [`/Users/vova_nguyen/Documents/ccc/backend`](/Users/vova_nguyen/Documents/ccc/backend)
- Django REST Framework and SimpleJWT configured
- Custom user model in `apps/accounts`
- Auth endpoints:
  - `POST /api/auth/register/`
  - `POST /api/auth/login/`
  - `POST /api/auth/refresh/`
  - `GET /api/auth/me/`
  - `GET /api/profile/`
  - `PATCH /api/profile/`
- CORS configured for the mobile client
- Basic backend auth test coverage

### Not Implemented
- Plans, calendar, reminders, and explore APIs
- Production deployment configuration
- Persistent media handling beyond the current profile fields
- Full backend test coverage across all apps

## Models and Data

### Implemented
- SwiftUI `User` and `AuthResponse` models for auth
- Local mock data still powers the legacy product screens
- Django `User` model supports the current auth/profile flows

### Not Implemented
- Real persistence for plans/events/places
- Sync, caching, or offline conflict handling
- A shared domain model layer between frontend and backend

## Testing

### Implemented
- Backend API test for register, login, me, and profile patch
- Successful iOS build in Xcode after the auth refactor

### Not Implemented
- Full UI test coverage for every screen
- Snapshot tests
- End-to-end auth test coverage from SwiftUI through backend
- Backend tests for non-auth features

## Summary

The current implementation is an auth-first rebuild:
- the backend now exists as a Django + DRF + JWT service with a custom user model
- the iOS app now boots through an auth gate and can register, log in, restore a session, fetch `me`, fetch profile, update profile, and log out
- the older Home, Calendar, Explore, and Place Detail screens still exist as legacy mock-data tabs, but they are not the focus of the current backend-first pass
