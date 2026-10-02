from typing import Literal, TypeAlias


MembershipRole: TypeAlias = Literal[
    "owner",
    "member",
    "collector",
]


def membership_role_allowed_for_product(
    *,
    role: MembershipRole,
    product_slug: str,
) -> bool:
    if role in {"owner", "member"}:
        return True

    return (
        role == "collector"
        and product_slug == "prestamodesk"
    )
