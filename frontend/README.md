# Frontend Notes

This frontend is the current Workbench app surface.

It is not the long-term marketing or landing page. If a separate public landing page is added later, this app should live behind a dedicated app route such as `/app`.

## Naming Direction

Current component names still use `landing` in several places. That is stale.

Preferred naming direction:
- `WorkbenchLanding` -> `WorkbenchApp`
- `components/landing/` -> `components/app/`
- `LandingSearchForm` -> `AppSearchForm`

`App.tsx` should remain the React root component and does not need to be renamed.

## Deployment Boundary

The browser must never call AWS Lambda directly.

Expected deployed request path:
- browser calls the Vercel app origin
- Vercel server-side function forwards requests to Lambda
- Lambda validates a server-side shared secret

No Lambda URL or backend secret should appear in client-side code.

## Access Model

The deployed app route is expected to be password protected.

That password gate controls access to the app surface itself. It is separate from the backend protection between Vercel and Lambda.
