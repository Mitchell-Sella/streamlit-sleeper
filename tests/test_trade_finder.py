import pytest
from app_pages.trade_finder import get_tier_value, clean_name, generate_trades

def test_get_tier_value():
    assert get_tier_value(1) == 3000
    assert get_tier_value(1.5) == 2500
    assert get_tier_value(3) == 1400
    assert get_tier_value(11) == 0
    assert get_tier_value(0.5) == 3000
    assert get_tier_value("invalid") == 0

def test_clean_name():
    assert clean_name("Ja'Marr Chase") == "jamarrchase"
    assert clean_name("T.J. Hockenson") == "tjhockenson"
    assert clean_name("D'Andre Swift") == "dandreswift"
    assert clean_name("Michael Pittman Jr.") == "michaelpittman"
    assert clean_name("Patrick Mahomes II") == "patrickmahomes"
    assert clean_name("A.J. Brown") == "ajbrown"
    assert clean_name("AJ Brown") == "ajbrown"
    assert clean_name("Kenneth Walker III") == "kennethwalker"
    assert clean_name("Travis Etienne Jr.") == "travisetienne"

def test_generate_trades():
    my_roster = {
        'players': [
            {'name': 'Player A', 'position': 'RB', 'value': 2000},
            {'name': 'Player B', 'position': 'RB', 'value': 1000},
            {'name': 'Player C', 'position': 'WR', 'value': 500}
        ]
    }
    other_roster = {
        'players': [
            {'name': 'Player X', 'position': 'WR', 'value': 1900},
            {'name': 'Player Y', 'position': 'WR', 'value': 1100},
            {'name': 'Player Z', 'position': 'RB', 'value': 300}
        ]
    }

    my_strengths = ['RB']
    my_weaknesses = ['WR']

    trades = generate_trades(my_roster, other_roster, my_strengths, my_weaknesses)

    # 1 for 1 fair trade: Player A (2000) for Player X (1900) - Diff 100, Avg 1950, 15% is 292.5 - FAIR
    # 2 for 1 fair trade: Player B + C? C is WR, so won't be included in strengths.

    assert len(trades) > 0

    trade1 = next(t for t in trades if len(t['give']) == 1 and len(t['receive']) == 1 and t['give'][0]['name'] == 'Player A')
    assert trade1['give'][0]['name'] == 'Player A'
    assert trade1['receive'][0]['name'] == 'Player X'

    trade2 = next(t for t in trades if len(t['give']) == 1 and len(t['receive']) == 1 and t['give'][0]['name'] == 'Player B')
    assert trade2['give'][0]['name'] == 'Player B'
    assert trade2['receive'][0]['name'] == 'Player Y'

    # Test Constraints
    trades_constrained = generate_trades(
        my_roster, other_roster, my_strengths, my_weaknesses,
        off_limits=['Player A'],
        force_receive=['Player Y']
    )

    assert len(trades_constrained) > 0
    # Every constrained trade must receive Player Y and must NOT give Player A
    for t in trades_constrained:
        give_names = [p['name'] for p in t['give']]
        receive_names = [p['name'] for p in t['receive']]
        assert 'Player A' not in give_names
        assert 'Player Y' in receive_names

def test_generate_trades_sizes():
    my_roster = {
        'players': [
            {'name': 'Player A', 'position': 'RB', 'value': 2000},
            {'name': 'Player B', 'position': 'RB', 'value': 1000},
            {'name': 'Player C', 'position': 'RB', 'value': 500}
        ]
    }
    other_roster = {
        'players': [
            {'name': 'Player X', 'position': 'WR', 'value': 1500},
            {'name': 'Player Y', 'position': 'WR', 'value': 1000},
            {'name': 'Player Z', 'position': 'WR', 'value': 800}
        ]
    }

    trades = generate_trades(
        my_roster, other_roster, ['RB'], ['WR'],
        max_give=3, max_receive=3
    )

    # Just verify it doesn't crash and returns some trades
    assert len(trades) > 0

    # Check that a 3 for 2 trade is theoretically possible if values match,
    # but at the very least sizes up to 3 exist in the raw generation before filtering.
    # Player A(2000)+B(1000)+C(500) = 3500. X(1500)+Y(1000)+Z(800) = 3300.
    # Avg 3400. Diff 200. 15% is 510. This is a fair trade!

    trade_3v3 = [t for t in trades if len(t['give']) == 3 and len(t['receive']) == 3]
    assert len(trade_3v3) > 0
