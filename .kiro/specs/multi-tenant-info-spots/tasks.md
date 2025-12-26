# Implementation Plan: Multi-Tenant Info Spots Platform

## Overview

This implementation plan breaks down the development of the multi-tenant QR/NFC-based information platform into discrete, manageable tasks. The plan follows an incremental approach, building core infrastructure first, then adding features layer by layer, with testing integrated throughout.

## Tasks

- [ ] 1. Set up project foundation and multi-tenancy infrastructure
  - Configure Django project with required dependencies (django-qr-code, Stripe, Redis, Hypothesis)
  - Create core models: Tenant, TenantAdmin, EndUser
  - Implement TenantMiddleware for subdomain-based tenant resolution
  - Set up thread-local storage for tenant context
  - Configure session management for cross-subdomain support
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 1.1 Write property test for tenant subdomain uniqueness
  - **Property 1: Tenant Subdomain Uniqueness**
  - **Validates: Requirements 1.1**

- [x] 1.2 Write property test for tenant data isolation
  - **Property 2: Tenant Data Isolation**
  - **Validates: Requirements 1.2, 1.3**

- [x] 1.3 Write property test for tenant deletion cascade
  - **Property 3: Tenant Deletion Cascade**
  - **Validates: Requirements 1.5**

- [ ] 2. Checkpoint - Verify multi-tenancy foundation
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 3. Implement shared end user authentication
  - Extend Django User model with EndUser profile
  - Configure django-allauth for authentication
  - Set up cross-subdomain session cookies
  - Create login, registration, and profile views
  - Implement HTMX-based authentication forms
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [ ] 3.1 Write property test for global user authentication
  - **Property 4: Global User Authentication**
  - **Validates: Requirements 2.1, 2.3**

- [ ] 3.2 Write property test for user profile global consistency
  - **Property 5: User Profile Global Consistency**
  - **Validates: Requirements 2.4, 2.5**

- [ ] 3.3 Write unit tests for authentication views
  - Test login, registration, logout flows
  - Test cross-subdomain session persistence
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 4. Create tenant admin interface
  - Implement TenantAdmin model and permissions
  - Create tenant admin dashboard view
  - Build tenant onboarding flow with setup wizard
  - Implement tenant branding configuration (logo, colors)
  - Create HTMX-based admin navigation
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 13.1, 13.2, 13.3, 13.4, 13.5, 18.1, 18.2, 18.3, 18.4, 18.5_

- [ ] 4.1 Write property test for tenant admin data association
  - **Property 10: Tenant Admin Data Association**
  - **Validates: Requirements 3.2, 3.4**

- [ ] 4.2 Write property test for tenant branding application
  - **Property 32: Tenant Branding Application**
  - **Validates: Requirements 18.1, 18.2, 18.3, 18.5**

- [ ] 4.3 Write unit tests for admin dashboard and onboarding
  - Test dashboard displays tenant-specific data
  - Test onboarding wizard completion
  - Test branding preview functionality
  - _Requirements: 3.1, 13.1, 13.2, 13.3, 13.4, 13.5, 18.4_

- [ ] 5. Checkpoint - Verify authentication and admin foundation
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement InfoSpot model and QR/NFC generation
  - Create InfoSpot model with UUID, access types, and tenant association
  - Implement QR code generation using django-qr-code
  - Create NFC tag identifier generation
  - Build QR code download endpoint for admins
  - Add QR code display in admin interface
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 6.1 Write property test for QR code uniqueness and round-trip
  - **Property 11: QR Code Uniqueness and Round-Trip**
  - **Validates: Requirements 4.1, 4.3, 4.4**

- [ ] 6.2 Write property test for NFC tag uniqueness and resolution
  - **Property 12: NFC Tag Uniqueness and Resolution**
  - **Validates: Requirements 4.2, 4.5**

- [ ] 6.3 Write unit tests for QR/NFC generation
  - Test QR code format and content
  - Test NFC tag generation
  - Test download endpoint
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 7. Implement content management system
  - Create Content model with multi-language support
  - Implement file upload validation for audio formats
  - Create content CRUD views for tenant admins
  - Build HTMX-based content editor with rich text support
  - Implement content versioning for offline support
  - Add file size validation
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 15.1, 15.2, 16.3, 16.5_

- [ ] 7.1 Write property test for audio format validation
  - **Property 13: Audio Format Validation**
  - **Validates: Requirements 7.1**

- [ ] 7.2 Write property test for multiple content per spot
  - **Property 14: Multiple Content Per Spot**
  - **Validates: Requirements 7.3**

- [ ] 7.3 Write property test for content update immediacy
  - **Property 15: Content Update Immediacy**
  - **Validates: Requirements 7.4**

- [ ] 7.4 Write property test for file size validation
  - **Property 16: File Size Validation**
  - **Validates: Requirements 7.5**

- [ ] 7.5 Write property test for multi-language content support
  - **Property 26: Multi-Language Content Support**
  - **Validates: Requirements 15.1, 15.2**

- [ ] 7.6 Write property test for content versioning
  - **Property 29: Content Versioning**
  - **Validates: Requirements 16.2, 16.5**

- [ ] 7.7 Write unit tests for content management
  - Test content creation with different file types
  - Test file upload validation
  - Test rich text formatting
  - Test version incrementing
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 8. Checkpoint - Verify content management
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement credit system models and logic
  - Create UserCredit model with balance tracking
  - Create CreditPurchase model for purchase transactions
  - Create CreditTransaction model for spending records
  - Implement atomic credit spending with database locks
  - Add credit balance display in user interface
  - _Requirements: 6.4, 6.5, 9.2, 9.4, 9.5_

- [ ] 9.1 Write property test for credit balance accuracy
  - **Property 18a: Credit Balance Accuracy**
  - **Validates: Requirements 9.2**

- [ ] 9.2 Write property test for no double charging
  - **Property 18b: No Double Charging**
  - **Validates: Requirements 6.5**

- [ ] 9.3 Write property test for credit purchase and transaction records
  - **Property 18: Credit Purchase and Transaction Records**
  - **Validates: Requirements 9.4, 9.5**

- [ ] 9.4 Write unit tests for credit system
  - Test credit balance calculations
  - Test atomic credit spending
  - Test concurrent spending with locks
  - Test double-charge prevention
  - _Requirements: 6.5, 9.2_

- [ ] 10. Integrate Stripe payment for credit purchases
  - Set up Stripe API configuration
  - Create credit package definitions (10, 20, 50 credits)
  - Implement PurchaseCreditsView with Stripe PaymentIntent
  - Create Stripe webhook handler for payment confirmation
  - Build HTMX-based credit purchase UI with Stripe Elements
  - Add credit purchase history view
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 10.1 Write integration tests for credit purchase flow
  - Test end-to-end credit purchase with Stripe test mode
  - Test webhook handling
  - Test payment failure scenarios
  - _Requirements: 9.1, 9.2, 9.3_

- [ ] 11. Checkpoint - Verify credit and payment system
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Implement info spot access control
  - Create InfoSpotAccessView with access type logic
  - Implement ticketed venue anonymous access
  - Implement public spot authentication requirement
  - Implement credit-based access gating for paid spots
  - Create SpendCreditsView for credit spending
  - Build HTMX-based access prompts (login, insufficient credits)
  - _Requirements: 5.1, 5.2, 5.3, 6.2, 6.3, 6.4, 6.5, 8.1, 8.2, 8.3_

- [ ] 12.1 Write property test for ticketed venue anonymous access
  - **Property 6: Ticketed Venue Anonymous Access**
  - **Validates: Requirements 5.1, 5.2, 5.3, 8.1**

- [ ] 12.2 Write property test for public spot authentication requirement
  - **Property 7: Public Spot Authentication Requirement**
  - **Validates: Requirements 2.2, 6.2, 8.2**

- [ ] 12.3 Write property test for credit-based access gating
  - **Property 8: Credit-Based Access Gating**
  - **Validates: Requirements 6.4, 8.3**

- [ ] 12.4 Write property test for credit spending unlocks content
  - **Property 9: Credit Spending Unlocks Content**
  - **Validates: Requirements 6.5, 9.2**

- [ ] 12.5 Write unit tests for access control logic
  - Test access control for each spot type
  - Test authentication redirects
  - Test credit spending flow
  - _Requirements: 5.1, 5.2, 5.3, 6.2, 6.3, 6.4, 6.5_

- [ ] 13. Build end user content viewing interface
  - Create spot detail view with content display
  - Implement audio player with controls (play, pause, seek, volume)
  - Create text content display with formatting
  - Build language switcher with HTMX
  - Implement language preference detection and fallback
  - Add access history view for authenticated users
  - _Requirements: 8.4, 8.5, 8.6, 15.3, 15.4, 15.5_

- [ ] 13.1 Write property test for access history tracking
  - **Property 17: Access History Tracking**
  - **Validates: Requirements 8.6**

- [ ] 13.2 Write property test for language preference matching
  - **Property 27: Language Preference Matching**
  - **Validates: Requirements 15.3, 15.4**

- [ ] 13.3 Write property test for language switching
  - **Property 28: Language Switching**
  - **Validates: Requirements 15.5**

- [ ] 13.4 Write unit tests for content viewing
  - Test audio player rendering
  - Test text formatting
  - Test language switching
  - Test access history display
  - _Requirements: 8.4, 8.5, 8.6, 15.3, 15.4, 15.5_

- [ ] 14. Checkpoint - Verify access control and content viewing
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Implement analytics and access tracking
  - Create SpotAccess model for tracking
  - Implement access event recording (anonymous for ticketed, identified for public)
  - Build analytics dashboard for tenant admins
  - Create access count and popularity ranking views
  - Implement time-based analytics (hour, day, month)
  - Add average consumption time calculation
  - _Requirements: 5.4, 6.6, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

- [ ] 15.1 Write property test for analytics access recording
  - **Property 22: Analytics Access Recording**
  - **Validates: Requirements 14.1, 14.2, 14.3, 5.4, 6.6**

- [ ] 15.2 Write property test for access count accuracy
  - **Property 23: Access Count Accuracy**
  - **Validates: Requirements 14.4**

- [ ] 15.3 Write property test for popularity ranking
  - **Property 24: Popularity Ranking**
  - **Validates: Requirements 14.6**

- [ ] 15.4 Write property test for average consumption time calculation
  - **Property 25: Average Consumption Time Calculation**
  - **Validates: Requirements 14.7**

- [ ] 15.5 Write unit tests for analytics
  - Test access event recording
  - Test anonymous vs identified tracking
  - Test time-based aggregation
  - Test ranking algorithm
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

- [ ] 16. Build tenant revenue management
  - Create revenue dashboard view
  - Implement transaction report generation
  - Add date range filtering for reports
  - Create analytics on free vs paid spot access
  - Implement CSV and PDF export for reports
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 16.1 Write property test for revenue calculation accuracy
  - **Property 19: Revenue Calculation Accuracy**
  - **Validates: Requirements 10.1**

- [ ] 16.2 Write property test for transaction report completeness
  - **Property 20: Transaction Report Completeness**
  - **Validates: Requirements 10.2**

- [ ] 16.3 Write property test for date range filtering
  - **Property 21: Date Range Filtering**
  - **Validates: Requirements 10.3**

- [ ] 16.4 Write unit tests for revenue management
  - Test revenue calculations
  - Test report generation
  - Test date filtering
  - Test export functionality
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 17. Checkpoint - Verify analytics and revenue management
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 18. Implement performance optimizations
  - Add database indexes for critical queries
  - Implement Redis caching for content and analytics
  - Set up template fragment caching
  - Configure CDN for static and media files
  - Optimize audio file streaming
  - Add cache invalidation on content updates
  - _Requirements: 11.1, 11.2, 11.3, 11.5_

- [ ] 18.1 Write unit tests for caching
  - Test cache key generation
  - Test cache invalidation
  - Test cache hit/miss behavior
  - _Requirements: 11.3_

- [ ] 19. Implement security features
  - Configure HTTPS enforcement
  - Implement CSRF protection for all forms
  - Set up rate limiting with django-ratelimit
  - Configure Content Security Policy headers
  - Implement password hashing verification
  - Add PCI DSS compliance checks (no card storage)
  - Create data deletion endpoint with analytics preservation
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [ ] 19.1 Write property test for rate limiting enforcement
  - **Property 30: Rate Limiting Enforcement**
  - **Validates: Requirements 17.4**

- [ ] 19.2 Write property test for data deletion with analytics preservation
  - **Property 31: Data Deletion with Analytics Preservation**
  - **Validates: Requirements 17.5**

- [ ] 19.3 Write unit tests for security features
  - Test HTTPS enforcement
  - Test CSRF protection
  - Test rate limiting
  - Test password hashing
  - Test data deletion
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [ ] 20. Build mobile-responsive UI with Bootstrap and HTMX
  - Create base template with Bootstrap 5
  - Implement responsive navigation
  - Build mobile-optimized spot detail page
  - Create touch-friendly controls (44x44px minimum)
  - Implement HTMX partial templates for dynamic updates
  - Add loading indicators for HTMX requests
  - Test responsive layouts on various screen sizes
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 20.1 Write unit tests for responsive UI
  - Test viewport meta tags
  - Test Bootstrap classes usage
  - Test HTMX attributes
  - Test touch target sizes
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 21. Checkpoint - Verify performance, security, and UI
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 22. Prepare for future mobile app integration
  - Create RESTful API endpoints with Django REST Framework
  - Implement JWT authentication for API
  - Add API versioning (v1)
  - Create content download endpoint for offline support
  - Implement sync endpoint with version tracking
  - Document API endpoints with OpenAPI/Swagger
  - _Requirements: 16.1, 16.2, 16.3, 16.4_

- [ ] 22.1 Write unit tests for API endpoints
  - Test API authentication
  - Test content download endpoint
  - Test sync endpoint
  - Test API versioning
  - _Requirements: 16.1, 16.2, 16.3_

- [ ] 23. Create comprehensive error handling
  - Implement custom error pages (404, 403, 500)
  - Add error logging with context (tenant, user, request ID)
  - Create user-friendly error messages
  - Implement HTMX error handling
  - Add toast notifications for non-blocking errors
  - Test all error scenarios
  - _Requirements: All error handling from design_

- [ ] 23.1 Write unit tests for error handling
  - Test error page rendering
  - Test error logging
  - Test HTMX error responses
  - Test validation errors

- [ ] 24. Final integration testing and deployment preparation
  - Run full test suite (unit + property + integration)
  - Verify all 34 correctness properties pass
  - Test cross-subdomain functionality
  - Test end-to-end user flows (registration → credit purchase → spot access)
  - Test end-to-end admin flows (onboarding → spot creation → analytics)
  - Configure production settings (DEBUG=False, ALLOWED_HOSTS, etc.)
  - Set up environment variables for deployment
  - Create deployment documentation
  - _Requirements: All requirements_

- [ ] 24.1 Write integration tests for complete user journeys
  - Test complete end user journey
  - Test complete tenant admin journey
  - Test multi-tenant isolation in production-like setup

- [ ] 25. Final checkpoint - Production readiness
  - Ensure all tests pass, ask the user if questions arise.
  - Verify deployment documentation is complete.
  - Confirm all environment variables are documented.

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at logical breakpoints
- Property tests validate universal correctness properties with minimum 100 iterations
- Unit tests validate specific examples, edge cases, and error conditions
- Integration tests validate end-to-end workflows
- The implementation follows an incremental approach: foundation → authentication → content → payments → access control → analytics → optimization
- HTMX is used throughout for dynamic interactions without full page reloads
- Bootstrap provides responsive, mobile-first UI components
- Atomic transactions with database locks prevent race conditions in credit spending
- All tests should pass before moving to the next checkpoint
