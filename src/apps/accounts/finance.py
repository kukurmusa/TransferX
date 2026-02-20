from decimal import Decimal

from .models import ClubFinance


def get_or_create_finance_for_user(user) -> ClubFinance:
    club = user.club
    finance, _ = ClubFinance.objects.get_or_create(club=club)
    return finance


def reserve(finance: ClubFinance, transfer_delta: Decimal, wage_delta: Decimal) -> None:
    finance.transfer_reserved += transfer_delta
    finance.wage_reserved_weekly += wage_delta
    finance.save(
        update_fields=["transfer_reserved", "wage_reserved_weekly", "updated_at"]
    )


def release(finance: ClubFinance, transfer_delta: Decimal, wage_delta: Decimal) -> None:
    finance.transfer_reserved = max(finance.transfer_reserved - transfer_delta, Decimal("0"))
    finance.wage_reserved_weekly = max(
        finance.wage_reserved_weekly - wage_delta, Decimal("0")
    )
    finance.save(
        update_fields=["transfer_reserved", "wage_reserved_weekly", "updated_at"]
    )


def commit(finance: ClubFinance, transfer_amount: Decimal, wage_amount: Decimal) -> None:
    finance.transfer_reserved = max(finance.transfer_reserved - transfer_amount, Decimal("0"))
    finance.wage_reserved_weekly = max(
        finance.wage_reserved_weekly - wage_amount, Decimal("0")
    )
    finance.transfer_committed += transfer_amount
    finance.wage_committed_weekly += wage_amount
    finance.save(
        update_fields=[
            "transfer_reserved",
            "wage_reserved_weekly",
            "transfer_committed",
            "wage_committed_weekly",
            "updated_at",
        ]
    )
