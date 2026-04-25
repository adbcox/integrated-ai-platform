# RM-UI-007

- **ID:** `RM-UI-007`
- **Title:** Cross-platform mobile companion app for platform control and monitoring
- **Category:** `UI`
- **Type:** `Feature`
- **Status:** `Completed`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `TBD`
- **Target horizon:** `later`
- **LOE:** `L-M`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `3`
- **Dependency burden:** `3`
- **Readiness:** `later`

## Description

Build a cross-platform mobile companion app (iOS and Android) for platform control, monitoring, and status access using Flutter as primary framework (with React Native as fallback for web-stack teams).

## Why it matters

Platform has web-first control center (RM-UI-001) and tablet displays (RM-UI-003/004) but lacks native mobile app with offline capabilities, push notifications, and mobile-optimized controls.

## Framework selection (2026 state)

**Primary: Flutter** - 46% adoption, single codebase for iOS/Android/desktop, production-ready
**Secondary: React Native** - 32% adoption, for teams with React expertise
**Tertiary: Ionic PWA** - Lightweight alternative without app store

**Decision rationale:**
- Flutter chosen for single codebase covering mobile + desktop (aligns with RM-UI-006)
- React Native if JavaScript expertise already present
- PWA for MVP/internal tools

## Key requirements

### Framework requirements
- Flutter SDK 3.26.0+ with Dart
- iOS (iPhone/iPad) + Android (phones/tablets)
- Optional desktop builds (Windows/macOS/Linux)
- Clean architecture or MVVM
- State management: Provider/Bloc/Riverpod
- Offline-first with SQLite

### Core features
- Authentication and session management
- Dashboard showing platform status
- Service quick controls
- System monitoring (CPU/RAM/Docker)
- Push notifications
- Biometric auth
- Dark mode
- Offline cache and sync

### API integration
- REST APIs from platform services
- RM-UI-006 dashboard platform data
- RM-UI-005 orchestration layer
- WebSocket for real-time updates
- JWT/OAuth tokens

### Security
- Secure token storage (Keychain/KeyStore)
- TLS/HTTPS all calls
- Certificate pinning (production)
- No hardcoded secrets

## Dependencies

- `RM-UI-006` - Dashboard platform APIs
- `RM-UI-001` - Control center APIs
- `RM-OPS-005` - Telemetry data
- Authentication system
- Push notification infrastructure

## External dependencies

### Flutter
- Docs: https://docs.flutter.dev/
- Desktop: https://docs.flutter.dev/platform-integration/desktop
- Version: 3.26.0+
- Adoption: `adopt-now` as primary

### React Native (alternative)
- Docs: https://reactnative.dev/
- Version: 0.73+ with New Architecture
- Adoption: `adopt-selective` if React expertise

## First milestone

1. Framework decision and environment setup
2. Authentication screen
3. Dashboard with 3-5 service tiles
4. Pull-to-refresh sync
5. Offline mode with cache
6. Dark mode
7. Beta builds (TestFlight/Play Internal Testing)

## Autonomous execution guidance

### Pre-implementation
1. Verify RM-UI-006 deployed with APIs
2. Confirm framework choice
3. Check auth endpoints available
4. Identify required services

### Implementation sequence (Flutter)
1. Install Flutter SDK 3.26.0+, configure emulators
2. `flutter create --platforms=ios,android integrated_ai_app`
3. Add dependencies: dio, provider/bloc, sqflite, flutter_secure_storage
4. Build login screen with JWT storage
5. Fetch platform status from RM-UI-006
6. Implement offline SQLite caching
7. Add dark mode and responsive layouts
8. Unit/widget/integration tests
9. Configure signing (iOS/Android)
10. CI/CD pipeline and beta distribution

### Completion contract
- Framework chosen and justified
- Authentication integrated
- Dashboard with live platform data
- Offline-first with caching
- Dark mode working
- Beta distributed to testers
- Development docs complete

## Status transition

- Next: `In Progress`
- Condition: RM-UI-006 APIs stable, framework chosen, auth ready
- Closeout: Beta deployed, core flows functional, offline working

## Notes

Flutter recommended for:
- Single codebase (mobile + desktop + web)
- Production-ready desktop support (2026)
- Pixel-perfect UI control
- 60fps performance

React Native viable if:
- Strong JavaScript/React team
- Web-to-mobile code reuse valuable
- Smaller app size needed
