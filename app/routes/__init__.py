from app.routes import customers, invoices, payments, plans, subscriptions

routers = [
    plans.router,
    customers.router,
    subscriptions.router,
    invoices.router,
    payments.router,
]
