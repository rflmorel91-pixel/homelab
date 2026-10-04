from typing import Literal, TypeAlias


MembershipRole: TypeAlias = Literal[
    "owner",
    "member",
    "collector",
    "administrator",
    "supervisor",
    "cashier",
]


def membership_role_allowed_for_product(
    *,
    role: MembershipRole,
    product_slug: str,
) -> bool:
    if role in {"owner", "member"}:
        return True

    return (
        role in {"collector", "administrator", "supervisor", "cashier"}
        and product_slug == "prestamodesk"
    )
