"""
Rank and Level Calculation Utilities

This module provides functions for calculating user ranks and XP requirements
based on the 7-rank progression system.
"""

def get_xp_for_level(level: int) -> int:
    """
    Calculate total XP needed to reach a specific level.
    
    Args:
        level: Target level (1-70)
    
    Returns:
        Total XP required to reach this level
    """
    if level <= 10:  # Novice
        return level * 100
    elif level <= 20:  # Challenger
        return 1000 + (level - 10) * 200
    elif level <= 30:  # Fighter
        return 3000 + (level - 20) * 350
    elif level <= 40:  # Warrior
        return 6500 + (level - 30) * 550
    elif level <= 50:  # Champion
        return 12000 + (level - 40) * 800
    elif level <= 60:  # Legend
        return 20000 + (level - 50) * 1200
    else:  # Mythic (61-70)
        return 32000 + (level - 60) * 1800


def calculate_level_from_xp(total_xp: int) -> int:
    """
    Calculate current level based on total XP earned.
    
    Args:
        total_xp: Total XP earned
    
    Returns:
        Current level (1-70)
    """
    for level in range(1, 71):
        if total_xp < get_xp_for_level(level):
            return level - 1
    return 70  # Max level


def calculate_rank(level: int, battle_count: int, battle_win_count: int) -> str:
    """
    Determine user's rank based on level and battle stats.
    User must meet BOTH level and battle requirements.
    
    Args:
        level: User's current level
        battle_count: Total battles fought
        battle_win_count: Total battles won
    
    Returns:
        Rank name (Novice, Challenger, Fighter, Warrior, Champion, Legend, Mythic)
    """
    win_rate = (battle_win_count / battle_count * 100) if battle_count > 0 else 0
    
    if level >= 61 and battle_count >= 200 and win_rate >= 65:
        return "Mythic"
    elif level >= 51 and battle_count >= 100 and win_rate >= 60:
        return "Legend"
    elif level >= 41 and battle_count >= 50 and win_rate >= 55:
        return "Champion"
    elif level >= 31 and battle_count >= 25 and win_rate >= 50:
        return "Warrior"
    elif level >= 21 and battle_count >= 10 and win_rate >= 40:
        return "Fighter"
    elif level >= 11 and battle_count >= 5:
        return "Challenger"
    else:
        return "Novice"


def get_next_rank_requirements(
    current_rank: str, 
    level: int, 
    battle_count: int, 
    battle_win_count: int
) -> dict:
    """
    Calculate what user needs to rank up to next tier.
    
    Args:
        current_rank: Current rank name
        level: Current level
        battle_count: Total battles
        battle_win_count: Total wins
    
    Returns:
        Dict with next rank name, progress indicators, and missing requirements
    """
    win_rate = (battle_win_count / battle_count * 100) if battle_count > 0 else 0
    
    requirements = {
        "Novice": {"level": 11, "battles": 5, "win_rate": 0},
        "Challenger": {"level": 21, "battles": 10, "win_rate": 40},
        "Fighter": {"level": 31, "battles": 25, "win_rate": 50},
        "Warrior": {"level": 41, "battles": 50, "win_rate": 55},
        "Champion": {"level": 51, "battles": 100, "win_rate": 60},
        "Legend": {"level": 61, "battles": 200, "win_rate": 65},
        "Mythic": {"level": 70, "battles": 500, "win_rate": 70}  # Cap
    }
    
    next_rank_map = {
        "Novice": "Challenger",
        "Challenger": "Fighter",
        "Fighter": "Warrior",
        "Warrior": "Champion",
        "Champion": "Legend",
        "Legend": "Mythic",
        "Mythic": "Mythic"  # Max rank
    }
    
    next_rank = next_rank_map[current_rank]
    req = requirements[next_rank]
    
    return {
        "next_rank": next_rank,
        "requirements": {
            "level": req["level"],
            "battles": req["battles"],
            "win_rate": req["win_rate"]
        },
        "progress": {
            "level": f"{level}/{req['level']}",
            "battles": f"{battle_count}/{req['battles']}",
            "win_rate": f"{win_rate:.1f}%/{req['win_rate']}%"
        },
        "missing": {
            "levels": max(0, req["level"] - level),
            "battles": max(0, req["battles"] - battle_count),
            "win_rate": max(0, req["win_rate"] - win_rate)
        },
        "is_eligible": (
            level >= req["level"] and 
            battle_count >= req["battles"] and 
            win_rate >= req["win_rate"]
        )
    }


def get_xp_progress(total_xp: int) -> dict:
    """
    Calculate XP progress toward next level.
    
    Args:
        total_xp: Total XP earned
    
    Returns:
        Dict with current level, XP progress, and percentage
    """
    current_level = calculate_level_from_xp(total_xp)
    current_level_xp = get_xp_for_level(current_level)
    next_level_xp = get_xp_for_level(current_level + 1)
    
    xp_progress = total_xp - current_level_xp
    xp_needed = next_level_xp - current_level_xp
    progress_percentage = (xp_progress / xp_needed * 100) if xp_needed > 0 else 100
    
    return {
        "current_level": current_level,
        "next_level": current_level + 1 if current_level < 70 else 70,
        "xp_progress": xp_progress,
        "xp_needed": xp_needed,
        "progress_percentage": round(progress_percentage, 1),
        "total_xp": total_xp
    }
