"""Deterministic, fictional dataset for the product tour."""

from backend.domain.relationship_service import RelationshipMap


def generate_demo_data() -> tuple[str, RelationshipMap, RelationshipMap]:
    root = "tu_perfil_demo"
    mutuals = {f"amigo_{index:03d}" for index in range(1, 71)}
    followers_only = {f"seguidor_{index:03d}" for index in range(1, 61)}
    following_only = {f"creador_{index:03d}" for index in range(1, 51)}

    following_map: RelationshipMap = {
        root: set(mutuals | following_only),
    }
    follower_map: RelationshipMap = {
        root: set(mutuals | followers_only),
    }

    all_profiles = sorted(mutuals | followers_only | following_only)
    for profile in all_profiles:
        following_map.setdefault(profile, set())
        follower_map.setdefault(profile, set())

    for profile in mutuals | following_only:
        follower_map[profile].add(root)
    for profile in mutuals | followers_only:
        following_map[profile].add(root)

    # Fictional connections make node expansion useful without external data.
    for index, profile in enumerate(all_profiles):
        for distance in (1, 7, 19):
            target = all_profiles[(index + distance) % len(all_profiles)]
            if target == profile:
                continue
            following_map[profile].add(target)
            follower_map[target].add(profile)

    return root, following_map, follower_map
