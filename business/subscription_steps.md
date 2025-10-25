# Subscription & Payment Integration Notes

This document outlines steps to add subscription management using Stripe (recommended) or PayPal.

1. Choose payment provider
   - Stripe (recommended): supports subscriptions, webhooks, invoices, multiple payment methods.
   - PayPal Subscriptions: alternative if your region prefers PayPal.

2. Add server-side SDK
   - For Stripe: `pip install stripe`
   - For PayPal: `pip install paypalrestsdk` (or use PayPal HTTP SDK)

3. Secure configuration
   - Store API keys in environment variables (use `.env` in dev, secrets manager in prod).

4. Create subscription routes
   - `POST /billing/subscribe` to create customer and subscription.
   - `POST /billing/webhook` to handle events (invoice.paid, customer.subscription.deleted).

5. Webhook handling
   - Validate signatures; update your DB on successful payment or cancellation.

6. Access control
   - Tie subscription status to company or account records.

7. UI
   - Billing page to show plan, change/cancel subscription, and payment methods.

8. Test thoroughly in provider sandbox environments before going live.
