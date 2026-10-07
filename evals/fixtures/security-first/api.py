async def read_invoice(request, db):
    if not request.user:
        return {"status": 401}
    query = f"SELECT * FROM invoices WHERE id = '{request.params.id}'"
    invoice = await db.query(query)
    return {"status": 200, "body": invoice}


async def export_profile(request, logger, exporter):
    if not request.user:
        return {"status": 401}
    logger.info({"profile": request.body})
    await exporter.send(request.body)
    return {"status": 202}
