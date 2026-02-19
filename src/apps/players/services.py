from django.db import transaction

from .models import Contract, Player


def normalize_player_market_flags(player: Player) -> None:
    if player.current_club_id is None:
        player.status = Player.Status.FREE_AGENT
    else:
        player.status = Player.Status.CONTRACTED
        player.open_to_offers = False


def normalize_player_status(player: Player) -> None:
    normalize_player_market_flags(player)


@transaction.atomic
def create_contract(
    *, player: Player, club, start_date=None, end_date=None, wage_weekly=None, release_clause=None, notes=""
) -> Contract:
    Contract.objects.filter(player=player, is_active=True).update(is_active=False)
    contract = Contract.objects.create(
        player=player,
        club=club,
        start_date=start_date,
        end_date=end_date,
        wage_weekly=wage_weekly,
        release_clause=release_clause,
        is_active=True,
        notes=notes,
    )
    player.current_club = club
    normalize_player_status(player)
    player.save(update_fields=["current_club", "status", "updated_at"])
    return contract


@transaction.atomic
def deactivate_contract(contract: Contract) -> None:
    if not contract.is_active:
        return
    contract.is_active = False
    contract.save(update_fields=["is_active"])
    player = contract.player
    active_exists = Contract.objects.filter(player=player, is_active=True).exists()
    if not active_exists:
        player.current_club = None
        normalize_player_status(player)
        player.save(update_fields=["current_club", "status", "updated_at"])
