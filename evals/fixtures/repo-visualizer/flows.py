async def submit_order(order, store, queue, fetch_payment):
    if not order.items:
        return {"status": "invalid"}
    for attempt in range(2):
        try:
            response = await fetch_payment(
                "https://payments.example.invalid/charge",
                {
                    "method": "POST",
                    "body": {"order_id": order.id, "amount": order.total},
                    "headers": {"Idempotency-Key": order.id},
                },
            )
            if response.status == 503 and attempt == 0:
                continue
            if not response.ok:
                return {"status": "declined"}
            await store.save_order(order)
            await queue.publish("order.paid", {"order_id": order.id})
            return {"status": "accepted"}
        except Exception:
            if attempt == 1:
                return {"status": "failed"}


async def fulfill_order(message, store):
    order = await store.get_order(message.order_id)
    await store.mark_shipped(order.id)
    return {"status": "shipped"}


def register_worker(queue, store):
    queue.subscribe("order.paid", lambda message: fulfill_order(message, store))


async def inventory_report(store):
    items = await store.list_inventory()
    return [
        {"sku": item.sku, "available": item.stock - item.reserved} for item in items
    ]
