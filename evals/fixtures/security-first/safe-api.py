import re


async def read_invoice(request, db):
    if not request.user:
        return {"status": 401}
    if not re.fullmatch(r"[0-9]{1,12}", request.params.id):
        return {"status": 400}
    invoice = await db.find_invoice(
        {
            "id": request.params.id,
            "tenant_id": request.user.tenant_id,
            "owner_id": request.user.id,
        }
    )
    if not invoice:
        return {"status": 404}
    return {"status": 200, "body": {"id": invoice.id, "total": invoice.total}}


# Fixture contract: trusted authentication middleware validates user identity.
# find_invoice is a parameterized query with all three predicates ANDed together.
# No alternate entry point or raw SQL path exists in this supplied scope.
